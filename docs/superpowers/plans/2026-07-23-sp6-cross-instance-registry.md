# SP6: Cross-Instance Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A self-maintaining global index (`~/.cairn/registry.json`) of all cairn instances, plus a `/cairn:list` skill for portfolio view, name→path routing, and read-only cross-instance peeks.

**Architecture:** Registry helpers live in `templates/hooks/cairn_lib.py` (copied into instances as today; imported plugin-side via `sys.path`). Two automatic writers: `scaffold.py` (at build) and `session_start.py` (every boot, fail-soft, before the concluded early-return). Status is derived at read time by a new deterministic script `skills/list/list_instances.py`; judgment (routing, peeks, confirmations) lives in `skills/list/SKILL.md`. The registry is a rebuildable cache — corrupt files are coerced fresh, never quarantined.

**Tech Stack:** python3 stdlib only, pytest (existing suite: 121 tests), markdown skill.

**Spec:** `docs/superpowers/specs/2026-07-23-sp6-cross-instance-registry-design.md`

---

### Task 1: Suite-wide `CAIRN_HOME` test isolation

No test may ever touch the real `~/.cairn/`. This must land BEFORE any code that writes the registry.

**Files:**
- Modify: `tests/conftest.py`

- [ ] **Step 1: Add an autouse fixture to conftest.py**

Append to `tests/conftest.py` (after the imports, before `MANIFEST`):

```python
@pytest.fixture(autouse=True)
def _cairn_home(tmp_path, monkeypatch):
    """Every test (and every subprocess it spawns) gets an isolated global registry.
    Guards the developer's real ~/.cairn/ from the whole suite (SP6 spec §4)."""
    home = tmp_path / "cairn-home"
    monkeypatch.setenv("CAIRN_HOME", str(home))
    return home
```

Note: `run_script` uses `subprocess.run` without an `env=` argument, so subprocesses inherit the patched environment automatically. No change to `run_script` needed.

- [ ] **Step 2: Run the full suite to verify nothing breaks**

Run: `python3 -m pytest tests/ -q`
Expected: all 121 tests pass (the fixture is inert until registry code exists).

- [ ] **Step 3: Commit**

```bash
git add tests/conftest.py
git commit -m "test: isolate CAIRN_HOME per-test before any registry code lands"
```

---

### Task 2: Registry helpers in `cairn_lib.py`

**Files:**
- Modify: `templates/hooks/cairn_lib.py`
- Create: `tests/test_registry.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_registry.py`:

```python
"""Registry helpers: rebuildable global index at $CAIRN_HOME/registry.json (SP6)."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "templates" / "hooks"))
import cairn_lib
from conftest import MANIFEST


def read_reg(home):
    return json.loads((home / "registry.json").read_text())


def test_upsert_creates_file_and_parents(instance, _cairn_home):
    assert cairn_lib.registry_upsert(instance) is True
    reg = read_reg(_cairn_home)
    entry = reg["instances"][str(instance.resolve())]
    assert reg["version"] == 1
    assert entry["name"] == "test-instance"
    assert entry["cairn_version"] == "0.1.0"
    assert entry["created"] == "2026-07-19"
    # +00:00 offset, never Z — same format as every event (now_iso)
    assert entry["last_session"].endswith("+00:00")


def test_upsert_purpose_falls_back_to_empty_on_pre_sp6_manifest(instance, _cairn_home):
    # conftest MANIFEST carries purpose (post-SP6); strip it to simulate an old instance
    m = json.loads((instance / "manifest.json").read_text())
    m["instance"].pop("purpose", None)
    (instance / "manifest.json").write_text(json.dumps(m))
    cairn_lib.registry_upsert(instance)
    assert read_reg(_cairn_home)["instances"][str(instance.resolve())]["purpose"] == ""


def test_upsert_updates_own_entry_without_touching_others(instance, _cairn_home):
    other = {"name": "other", "purpose": "p", "created": "2026-01-01",
             "last_session": "2026-01-01T00:00:00+00:00", "cairn_version": "0.5.0"}
    (_cairn_home).mkdir(parents=True)
    (_cairn_home / "registry.json").write_text(json.dumps(
        {"version": 1, "instances": {"/elsewhere/other": other}}))
    cairn_lib.registry_upsert(instance)
    reg = read_reg(_cairn_home)
    assert reg["instances"]["/elsewhere/other"] == other
    assert str(instance.resolve()) in reg["instances"]


def test_corrupt_registry_coerced_fresh_not_crash(instance, _cairn_home):
    _cairn_home.mkdir(parents=True)
    (_cairn_home / "registry.json").write_text("{not json")
    assert cairn_lib.registry_upsert(instance) is True
    reg = read_reg(_cairn_home)
    assert list(reg["instances"]) == [str(instance.resolve())]


def test_non_object_registry_coerced_fresh(instance, _cairn_home):
    _cairn_home.mkdir(parents=True)
    (_cairn_home / "registry.json").write_text("5")
    assert cairn_lib.registry_upsert(instance) is True
    assert str(instance.resolve()) in read_reg(_cairn_home)["instances"]


def test_upsert_fail_soft_on_unwritable_home(instance, _cairn_home, monkeypatch):
    # a FILE where the directory should be makes mkdir/replace fail
    _cairn_home.parent.mkdir(parents=True, exist_ok=True)
    _cairn_home.write_text("i am a file, not a dir")
    assert cairn_lib.registry_upsert(instance) is False  # returns, never raises


def test_registry_remove(instance, _cairn_home):
    cairn_lib.registry_upsert(instance)
    assert cairn_lib.registry_remove(str(instance.resolve())) is True
    assert read_reg(_cairn_home)["instances"] == {}


def test_no_temp_files_left_behind(instance, _cairn_home):
    cairn_lib.registry_upsert(instance)
    leftovers = [p for p in _cairn_home.iterdir() if p.name != "registry.json"]
    assert leftovers == []
```

Also add `"purpose": "Test things end to end"` to the `instance` object in `tests/conftest.py`'s `MANIFEST` dict (spec §2):

```python
    "instance": {"name": "test-instance", "created": "2026-07-19",
                 "purpose": "Test things end to end"},
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_registry.py -q`
Expected: FAIL — `AttributeError: module 'cairn_lib' has no attribute 'registry_upsert'`

- [ ] **Step 3: Implement the helpers**

Append to `templates/hooks/cairn_lib.py`:

```python
# --- global registry (SP6): a rebuildable cache of instance pointers, never state ---

def registry_path():
    return Path(os.environ.get("CAIRN_HOME", str(Path.home() / ".cairn"))) / "registry.json"

def load_registry():
    """Well-formed registry dict, or a fresh empty one. Corrupt/non-object files are
    coerced — the registry is a cache; instances re-register on their next boot."""
    try:
        data = json.loads(registry_path().read_text())
        if isinstance(data, dict) and isinstance(data.get("instances"), dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {"version": 1, "instances": {}}

def _write_registry(reg):
    p = registry_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".registry-{os.getpid()}.tmp")  # pid-unique: concurrent boots can't collide
    tmp.write_text(json.dumps(reg, indent=2) + "\n")
    os.replace(tmp, p)

def registry_upsert(root):
    """Upsert this instance into the global registry. Fail-soft: returns bool, never raises.
    Read-modify-write is not locked; a lost race costs one stale field until the next boot."""
    try:
        m = manifest(root)
        inst = m.get("instance") if isinstance(m.get("instance"), dict) else {}
        reg = load_registry()
        reg["instances"][str(Path(root).resolve())] = {
            "name": inst.get("name", ""),
            "purpose": inst.get("purpose", ""),
            "created": inst.get("created", ""),
            "last_session": now_iso(),
            "cairn_version": m.get("cairn_version", ""),
        }
        _write_registry(reg)
        return True
    except Exception:
        return False

def registry_remove(path):
    """Drop one entry (user-confirmed prune). Fail-soft: returns bool, never raises."""
    try:
        reg = load_registry()
        if reg["instances"].pop(path, None) is None:
            return False
        _write_registry(reg)
        return True
    except Exception:
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_registry.py tests/test_cairn_lib.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add templates/hooks/cairn_lib.py tests/test_registry.py tests/conftest.py
git commit -m "feat(registry): cairn_lib registry helpers — atomic, fail-soft, coerce-fresh"
```

---

### Task 3: Boot-time upsert in `session_start.py`

**Files:**
- Modify: `templates/hooks/session_start.py:5` (import) and `templates/hooks/session_start.py:42-44` (call site)
- Modify: `tests/test_session_start.py` (append tests)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_session_start.py` (it already imports `run_script`/`instance` conventions from conftest; match its existing payload style — check the file's first test for the exact payload shape and reuse it):

```python
def test_boot_upserts_registry(instance, _cairn_home):
    run_script("session_start.py", {"cwd": str(instance), "session_id": "s-reg"})
    reg = json.loads((_cairn_home / "registry.json").read_text())
    entry = reg["instances"][str(instance.resolve())]
    assert entry["name"] == "test-instance"
    assert entry["last_session"].endswith("+00:00")


def test_concluded_instance_still_upserts_but_stays_silent(instance, _cairn_home):
    m = json.loads((instance / "manifest.json").read_text())
    m["instance"]["concluded"] = True
    (instance / "manifest.json").write_text(json.dumps(m))
    r = run_script("session_start.py", {"cwd": str(instance), "session_id": "s-conc"})
    assert r.stdout.strip() == ""  # silent, as today
    reg = json.loads((_cairn_home / "registry.json").read_text())
    assert str(instance.resolve()) in reg["instances"]  # but still self-heals


def test_unwritable_registry_never_costs_the_banner(instance, _cairn_home):
    _cairn_home.parent.mkdir(parents=True, exist_ok=True)
    _cairn_home.write_text("file blocking the dir")
    r = run_script("session_start.py", {"cwd": str(instance), "session_id": "s-bad"})
    out = json.loads(r.stdout)
    assert "cairn boot:" in out["systemMessage"]  # banner intact
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_session_start.py -q`
Expected: the three new tests FAIL (no registry file / KeyError); existing ones PASS.

- [ ] **Step 3: Implement**

In `templates/hooks/session_start.py`, change line 5 to:

```python
from cairn_lib import find_root, manifest, append_event, parse_ts, registry_upsert
```

And in `main()`, insert the upsert between `m = manifest(root)` and the concluded check (spec §3: concluded instances still refresh `last_session` and self-heal moves; `registry_upsert` catches everything internally so the banner can never be lost to it):

```python
    m = manifest(root)
    registry_upsert(root)   # global index refresh — fail-soft inside, never costs the banner
    if m.get("instance", {}).get("concluded"):
        return  # concluded instances stay silent: readable, never nagging
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_session_start.py tests/test_e2e.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add templates/hooks/session_start.py tests/test_session_start.py
git commit -m "feat(registry): boot-time upsert — self-registers, self-heals, never costs the banner"
```

---

### Task 4: Scaffold writes `purpose` to manifest and registers the instance

**Files:**
- Modify: `skills/build/scaffold.py:34-36` (imports), `:125` (manifest instance object), `:140-141` (post-manifest registration)
- Modify: `tests/test_scaffold.py` (append tests; reuse its existing minimal-config fixture — check the top of the file for the config dict it already uses)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_scaffold.py` (adapt the config/invocation names to the file's existing helpers — it already scaffolds into tmp dirs; the assertions below are the contract):

```python
def test_manifest_carries_purpose(tmp_path, _cairn_home):
    target = scaffold_ok(tmp_path)  # the file's existing happy-path helper/pattern
    m = json.loads((target / "manifest.json").read_text())
    assert m["instance"]["purpose"] == CONFIG["one_line_purpose"]


def test_scaffold_registers_instance(tmp_path, _cairn_home):
    target = scaffold_ok(tmp_path)
    reg = json.loads((_cairn_home / "registry.json").read_text())
    assert str(target.resolve()) in reg["instances"]


def test_registry_failure_warns_but_scaffold_succeeds(tmp_path, _cairn_home):
    _cairn_home.parent.mkdir(parents=True, exist_ok=True)
    _cairn_home.write_text("file blocking the dir")
    target, result = scaffold_run(tmp_path)  # pattern returning the CompletedProcess
    assert result.returncode == 0
    assert (target / "manifest.json").is_file()
    assert "registry" in result.stderr.lower()
```

If `test_scaffold.py` has no reusable helper, write the config inline exactly as the file's first test does and invoke `scaffold.py` via subprocess the same way.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_scaffold.py -q`
Expected: new tests FAIL (`KeyError: 'purpose'`, missing registry file).

- [ ] **Step 3: Implement**

In `skills/build/scaffold.py`:

(a) after the existing imports (line ~34), add the plugin-side import — the first ever, one line of path setup (spec §3):

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "templates" / "hooks"))
import cairn_lib
```

(b) change the manifest `instance` object (line ~125) to:

```python
        "instance": {"name": cfg["instance_name"], "created": today,
                     "purpose": cfg["one_line_purpose"]},
```

(c) after `(target / "manifest.json").write_text(...)` and before the final `print`, add — the one deliberate exception to scaffold's hard-failure contract, because the instance is fine and will self-register on first boot:

```python
    if not cairn_lib.registry_upsert(target):
        print("warning: could not update global registry — instance will "
              "self-register on first boot", file=sys.stderr)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_scaffold.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add skills/build/scaffold.py tests/test_scaffold.py
git commit -m "feat(registry): scaffold writes instance.purpose and registers at build"
```

---

### Task 5: `list_instances.py` — deterministic portfolio read + status derivation

**Files:**
- Create: `skills/list/list_instances.py`
- Create: `tests/test_list_instances.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_list_instances.py`:

```python
"""list_instances.py: registry read, live status derivation, prune/register (SP6 §6)."""
import json, subprocess, sys
from pathlib import Path
from conftest import MANIFEST

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "skills" / "list" / "list_instances.py"


def run_list(*argv):
    return subprocess.run([sys.executable, str(SCRIPT), *argv],
                          capture_output=True, text=True)


def make_instance(tmp_path, name, events=(), concluded=False):
    root = tmp_path / name
    (root / "telemetry").mkdir(parents=True)
    (root / "state").mkdir()
    m = json.loads(json.dumps(MANIFEST))
    m["instance"]["name"] = name
    if concluded:
        m["instance"]["concluded"] = True
    (root / "manifest.json").write_text(json.dumps(m))
    (root / "state" / "HOT.md").write_text("# HOT\nLast reconciled: 2026-07-19\n")
    (root / "telemetry" / "events.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in events))
    return root


def seed_registry(home, *roots):
    home.mkdir(parents=True, exist_ok=True)
    (home / "registry.json").write_text(json.dumps({"version": 1, "instances": {
        str(r.resolve()): {"name": r.name, "purpose": "p", "created": "2026-07-19",
                           "last_session": "2026-07-23T10:00:00+00:00",
                           "cairn_version": "0.8.0"} for r in roots}}))


TS = "2026-07-20T10:00:{s:02d}+00:00"
SUSPEND = {"ts": TS.format(s=1), "type": "lapse", "cause": "suspended", "deliberate": "true"}
SESSION_END = {"ts": TS.format(s=2), "type": "session", "phase": "end", "session_id": "x"}
LATER_START = {"ts": TS.format(s=3), "type": "session", "phase": "start", "session_id": "y"}


def test_active_suspended_concluded_missing(tmp_path, _cairn_home):
    active = make_instance(tmp_path, "active-one")
    suspended = make_instance(tmp_path, "susp-one", events=[SUSPEND, SESSION_END])
    concluded = make_instance(tmp_path, "conc-one", events=[SUSPEND], concluded=True)
    ghost = tmp_path / "ghost"  # registered but nothing on disk
    seed_registry(_cairn_home, active, suspended, concluded)
    reg = json.loads((_cairn_home / "registry.json").read_text())
    reg["instances"][str(ghost)] = {"name": "ghost", "purpose": "", "created": "",
                                    "last_session": "", "cairn_version": ""}
    (_cairn_home / "registry.json").write_text(json.dumps(reg))

    out = json.loads(run_list("--json").stdout)
    by_name = {e["name"]: e for e in out}
    assert by_name["active-one"]["status"] == "active"
    # manifest concluded flag is authoritative — beats the suspend event in its tail
    assert by_name["conc-one"]["status"] == "concluded"
    # session_end AFTER suspend must NOT flip it back to active (the tail hazard)
    assert by_name["susp-one"]["status"] == "suspended"
    assert by_name["ghost"]["status"] == "missing"


def test_session_start_after_suspend_means_active(tmp_path, _cairn_home):
    inst = make_instance(tmp_path, "resumed", events=[SUSPEND, SESSION_END, LATER_START])
    seed_registry(_cairn_home, inst)
    out = json.loads(run_list("--json").stdout)
    assert out[0]["status"] == "active"


def test_skipped_lapse_is_not_suspended(tmp_path, _cairn_home):
    skipped = dict(SUSPEND, cause="skipped")
    inst = make_instance(tmp_path, "skipper", events=[skipped])
    seed_registry(_cairn_home, inst)
    out = json.loads(run_list("--json").stdout)
    assert out[0]["status"] == "active"


def test_prune_removes_only_on_flag(tmp_path, _cairn_home):
    inst = make_instance(tmp_path, "real")
    seed_registry(_cairn_home, inst)
    ghost_path = str(tmp_path / "gone")
    reg = json.loads((_cairn_home / "registry.json").read_text())
    reg["instances"][ghost_path] = {"name": "gone", "purpose": "", "created": "",
                                    "last_session": "", "cairn_version": ""}
    (_cairn_home / "registry.json").write_text(json.dumps(reg))

    run_list("--json")  # a plain list never prunes
    reg = json.loads((_cairn_home / "registry.json").read_text())
    assert ghost_path in reg["instances"]

    r = run_list("--prune", ghost_path)
    assert r.returncode == 0
    reg = json.loads((_cairn_home / "registry.json").read_text())
    assert ghost_path not in reg["instances"]


def test_register_flag(tmp_path, _cairn_home):
    inst = make_instance(tmp_path, "manual")
    r = run_list("--register", str(inst))
    assert r.returncode == 0
    reg = json.loads((_cairn_home / "registry.json").read_text())
    assert str(inst.resolve()) in reg["instances"]


def test_last_reconciled_surfaced(tmp_path, _cairn_home):
    inst = make_instance(tmp_path, "stampy")
    seed_registry(_cairn_home, inst)
    out = json.loads(run_list("--json").stdout)
    assert out[0]["last_reconciled"] == "2026-07-19"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_list_instances.py -q`
Expected: FAIL — script does not exist.

- [ ] **Step 3: Implement `skills/list/list_instances.py`**

```python
#!/usr/bin/env python3
"""Deterministic reader for /cairn:list. Registry + live per-instance reads → JSON.
Usage: list_instances.py --json | --prune <path> | --register <root>
Plugin-side. Status derivation (SP6 spec §6), precedence order:
  concluded  <- manifest.instance.concluded (authoritative; /conclude sets it)
  suspended  <- last lapse event with deliberate=="true" and cause=="suspended",
                with no `session phase=start` after it (cairn_event stores values as
                strings; a same-session `session phase=end` after the suspend must
                NOT read as activity — that is the tail hazard)
  active     <- otherwise
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "templates" / "hooks"))
from cairn_lib import load_registry, manifest, parse_ts, registry_remove, registry_upsert


def load_events(root):
    p = Path(root) / "telemetry" / "events.jsonl"
    if not p.is_file():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict) and "type" in e and parse_ts(e.get("ts")) is not None:
            out.append(e)
    return out


def status_of(root):
    m = manifest(root)
    inst = m.get("instance") if isinstance(m.get("instance"), dict) else {}
    if inst.get("concluded"):
        return "concluded"
    evs = load_events(root)
    suspends = [e for e in evs if e["type"] == "lapse"
                and e.get("deliberate") == "true" and e.get("cause") == "suspended"]
    if suspends:
        t = parse_ts(suspends[-1]["ts"])
        resumed = any(e for e in evs if e["type"] == "session" and e.get("phase") == "start"
                      and parse_ts(e["ts"]) > t)
        if not resumed:
            return "suspended"
    return "active"


def last_reconciled(root):
    hot = Path(root) / "state" / "HOT.md"
    if not hot.is_file():
        return ""
    mo = re.search(r"^Last reconciled:\s*(\S+)", hot.read_text(), re.MULTILINE)
    return mo.group(1) if mo else ""


def entry_for(path, reg_entry):
    root = Path(path)
    if not (root / "manifest.json").is_file():
        return {"path": path, "name": reg_entry.get("name", ""),
                "purpose": reg_entry.get("purpose", ""), "status": "missing",
                "last_session": reg_entry.get("last_session", ""), "last_reconciled": "",
                "north_star": ""}
    m = manifest(root)
    metrics = m.get("metrics") if isinstance(m.get("metrics"), dict) else {}
    ns = metrics.get("north_star") if isinstance(metrics.get("north_star"), dict) else {}
    return {"path": path, "name": reg_entry.get("name", ""),
            "purpose": reg_entry.get("purpose", ""), "status": status_of(root),
            "last_session": reg_entry.get("last_session", ""),
            "last_reconciled": last_reconciled(root), "north_star": ns.get("name", "")}


def main():
    args = sys.argv[1:]
    if args[:1] == ["--prune"] and len(args) == 2:
        sys.exit(0 if registry_remove(args[1]) else 1)
    if args[:1] == ["--register"] and len(args) == 2:
        sys.exit(0 if registry_upsert(args[1]) else 1)
    reg = load_registry()
    out = [entry_for(p, e) for p, e in sorted(reg["instances"].items())]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_list_instances.py -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add skills/list/list_instances.py tests/test_list_instances.py
git commit -m "feat(registry): list_instances.py — live status derivation, prune/register"
```

---

### Task 6: `/cairn:list` skill — portfolio, routing, peeks

**Files:**
- Create: `skills/list/SKILL.md`

- [ ] **Step 1: Write the skill**

Create `skills/list/SKILL.md`:

```markdown
---
name: list
description: Portfolio view of every cairn instance on this machine — status, routing by name, read-only peeks into another instance
---

# /cairn:list — the registry

The global registry (`~/.cairn/registry.json`, or `$CAIRN_HOME/registry.json`) is a
rebuildable cache of instance pointers — names, paths, timestamps, never state. Instances
maintain it themselves at scaffold and every boot. Everything durable lives in each
instance's own files; this skill only ever READS instances.

## Portfolio view (default)

Run:

    python3 "${CLAUDE_PLUGIN_ROOT}/skills/list/list_instances.py" --json

Render one table from the JSON: **name · purpose · status · last session · last reconciled**.
Rules:
- Status is computed by the script (concluded ← manifest flag; suspended ← deliberate
  suspend lapse with no session start after it; else active). Do not re-derive it.
- Names may collide — when two entries share a name, show the path to disambiguate.
- **Never guilt (P13):** report status plainly. No "neglected for N days", no streaks,
  no nudges to return. A suspended or concluded system is an honorable state.
- An entry with status `missing` renders as "missing — moved or deleted?". Offer removal;
  only on explicit user confirmation run:
      python3 "${CLAUDE_PLUGIN_ROOT}/skills/list/list_instances.py" --prune "<path>"
  The user is the gate. Never auto-prune.
- If the current working directory is inside a cairn instance that is NOT in the registry
  (pre-0.8.0 instance), offer once: "register this instance?" On yes:
      python3 "${CLAUDE_PLUGIN_ROOT}/skills/list/list_instances.py" --register "<root>"
  Never walk the filesystem looking for unregistered instances.

## Routing ("open my job system")

Resolve the user's phrase against `name` and `purpose` (substring match, case-insensitive).
- One match → hand over the path: "your job-search instance is at <path> — open a session
  there to work in it."
- Multiple matches → show the candidates, the user picks.
- Routing is resolution, NOT teleportation: an instance's hooks, banner, and telemetry
  exist only in a session opened in its own directory. Never simulate working inside
  another instance from here; offer a peek instead if they just want to know where
  things stand.

## Peeks (read-only, P3)

When the user asks what another instance says / where it stands:
1. Resolve it via the registry (routing rules above).
2. Spawn a subagent that reads ONLY that instance's `state/HOT.md` and `manifest.json`
   and returns a condensed summary (~1-2K tokens): where things stand, north star, status.
3. Relay the summary. The other instance's files never enter this session's main context.

Hard rule: peeks never write. Not files, not telemetry, nothing — the target instance's
history must not show a session it didn't have. If a peek is asked to change something
("mark my job system suspended"), decline and route instead: that action belongs to a
session opened in that instance. Overreach is a telemetry-visible failure mode
(`failure_mode=overreach`) — log it in the CURRENT instance if you catch yourself.
```

- [ ] **Step 2: Sanity-check the skill loads**

Run: `python3 -c "import re,sys; t=open('skills/list/SKILL.md').read(); assert t.startswith('---') and 'name: list' in t.split('---')[1], 'frontmatter'; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add skills/list/SKILL.md
git commit -m "feat(registry): /cairn:list skill — portfolio, routing, read-only peeks"
```

---

### Task 7: Version bump, README privacy line, CHANGELOG

**Files:**
- Modify: `.claude-plugin/plugin.json` (version → 0.8.0)
- Modify: `README.md` ("What Cairn executes on your machine" section + command table)
- Modify: `CHANGELOG.md` (new 0.8.0 entry at top)

- [ ] **Step 1: Bump plugin version**

In `.claude-plugin/plugin.json`, change `"version": "0.7.1"` to `"version": "0.8.0"`.

- [ ] **Step 2: README — privacy line and command row**

In `README.md`, "What Cairn executes on your machine" section, after the "**Network: never.**" bullet, add:

```markdown
- **One global metadata file:** `~/.cairn/registry.json` — instance names, paths, and
  timestamps only, so `/cairn:list` can show you all your systems. `cat` it any time;
  delete it and instances re-register on their next boot. Still zero global hooks.
```

In the command table ("The commands" section), after the `/cairn:upgrade` row, add:

```markdown
| `/cairn:list` | Portfolio view of every instance on this machine — status (active/suspended/concluded), routing by name ("open my job system"), and read-only peeks into another instance's state. |
```

- [ ] **Step 3: CHANGELOG entry**

Add at the top of `CHANGELOG.md` (below the `# Changelog` line):

```markdown
## 0.8.0 — SP6: cross-instance registry

Multiple instances are now discoverable: a rebuildable global index at
`~/.cairn/registry.json` (pointers only — names, paths, timestamps; never state) that
instances maintain themselves at scaffold and every boot.

- **`/cairn:list`** — portfolio view (name · purpose · status · last session), name→path
  routing ("open my job system"), and read-only cross-instance peeks via condensed-return
  subagents (P3). Peeks never write; single-writer discipline is untouched.
- **`manifest.instance.purpose`** — new field (the interview's one-line purpose), so the
  registry and list can show what each system is for. Pre-0.8.0 manifests fall back to "".
- **Self-healing by design** — the registry is a cache: corrupt files are coerced fresh,
  moved instances re-register on next boot, deleting the file loses nothing. Existing
  instances join after `/cairn:upgrade` (hooks are copied wholesale) or via an explicit
  register offer in `/cairn:list`. No filesystem scanning, ever.
- **Privacy** — one new global metadata file, documented in the README; metadata only,
  local only, `cat`-able. Zero global hooks, unchanged.
- **Test isolation** — the suite exports `CAIRN_HOME` per-test; no test can touch a real
  registry.
```

- [ ] **Step 4: Full suite + commit**

Run: `python3 -m pytest tests/ -q`
Expected: all tests pass (121 pre-existing + ~17 new).

```bash
git add .claude-plugin/plugin.json README.md CHANGELOG.md
git commit -m "chore: 0.8.0 — cross-instance registry release notes, README privacy line"
```

---

## Self-review notes

- Spec §1 (schema/coerce-fresh) → Task 2. §2 (manifest purpose) → Tasks 2 (fixture) + 4. §3 (two writers, placement, plugin-side import) → Tasks 3 + 4. §4 (test isolation) → Task 1, deliberately first. §5 (upgrade/register paths) → Task 6 skill text; upgrade needs no code change (hooks copied wholesale — verified). §6 (list + status precedence) → Tasks 5 + 6. §7 (routing) / §8 (peeks) → Task 6. §9 (README) → Task 7. Release section → Task 7.
- Tasks 3 and 4 reference existing test files' local conventions (payload shape, scaffold helpers) — the implementer must read the target test file first and adapt names, keeping the assertions as written.
- Type consistency: `registry_upsert(root)` takes a path-like and returns bool everywhere; `list_instances.py --json` prints a JSON array of objects with keys `path,name,purpose,status,last_session,last_reconciled,north_star`.
```
