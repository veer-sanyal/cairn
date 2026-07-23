# SP3: Builder + Governor Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the level-zero doctrine into behavior: three deterministic sweep checks in validate.py, scaffolder passthrough for census/data_paths/boundary, builder stages for census + ladder + pass^k probes + boundary interview, governor sweeps + failure audit + de-automation rule.

**Architecture:** Detection is deterministic (validate.py, already run at review Stage 1, report-only fail-soft); disposition is model judgment (skill doctrine) gated by the user. Zero new event schema — `cairn_event.py` already takes arbitrary key=val, so failure tags are documentation. Spec: `docs/superpowers/specs/2026-07-23-sp3-builder-governor-wiring-design.md` (its "Design decisions" bind every task). Doctrine references: P16–P24 in docs/PRINCIPLES.md.

**Tech Stack:** python3 stdlib, pytest, markdown skills.

**Skill-edit tasks (3, 4):** these are insertions into living skill files. The plan gives verbatim blocks + named anchors; the implementer must read the whole target file first and place blocks so the stage flow reads coherently, then the reviewer checks end-to-end coherence. Existing test tokens in test_skills_exist.py must keep passing.

---

### Task 1: validate.py sweep checks

**Files:**
- Modify: `templates/hooks/validate.py`
- Create: `tests/test_validate_sweeps.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_validate_sweeps.py`:

```python
import json, datetime
from conftest import run_script

def valid(instance):
    r = run_script("validate.py", argv=["--json"], cwd=instance)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)

def checks(instance, name):
    return [f for f in valid(instance) if f["check"] == name]

def set_manifest(instance, **patch):
    m = json.loads((instance / "manifest.json").read_text())
    m.update(patch)
    (instance / "manifest.json").write_text(json.dumps(m))

def days_ago(n):
    return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()

def test_research_expired(instance):
    (instance / "docs").mkdir()
    (instance / "docs" / "RESEARCH.md").write_text(
        f"## a — researched 2026-01-01\nPerishability: perishable · Refresh-by: {days_ago(10)} · Engine: x\n\n"
        f"## b — researched 2026-01-01\nPerishability: durable · Refresh-by: on contradiction · Engine: x\n\n"
        f"## c — researched 2026-01-01\nPerishability: semi-durable · Refresh-by: {days_ago(-100)} · Engine: x\n")
    found = checks(instance, "research_expired")
    assert len(found) == 1 and found[0]["refresh_by"] == days_ago(10)

def test_no_research_file_is_silent(instance):
    assert checks(instance, "research_expired") == []

def test_census_stale_and_fresh(instance):
    set_manifest(instance, census={"date": days_ago(200), "mcp_servers": []})
    assert len(checks(instance, "census_stale")) == 1
    set_manifest(instance, census={"date": days_ago(10), "mcp_servers": []})
    assert checks(instance, "census_stale") == []

def test_data_paths_without_census_flags(instance):
    set_manifest(instance, data_paths=[{"need": "x", "rung": 4, "why": "y", "date": days_ago(1)}])
    assert len(checks(instance, "census_stale")) == 1

def test_legacy_manifest_silent(instance):
    # conftest MANIFEST has no census/data_paths/last_revalidated: all three sweeps silent
    for name in ["research_expired", "census_stale", "proxy_revalidation_due"]:
        assert checks(instance, name) == [], name

def test_proxy_revalidation_due_and_fresh(instance):
    m = json.loads((instance / "manifest.json").read_text())
    m["metrics"]["last_revalidated"] = days_ago(400)
    m["cadence"]["proxy_revalidation_days"] = 365
    (instance / "manifest.json").write_text(json.dumps(m))
    assert len(checks(instance, "proxy_revalidation_due")) == 1
    m["metrics"]["last_revalidated"] = days_ago(30)
    (instance / "manifest.json").write_text(json.dumps(m))
    assert checks(instance, "proxy_revalidation_due") == []

def test_malformed_dates_never_break_validator(instance):
    (instance / "docs").mkdir()
    (instance / "docs" / "RESEARCH.md").write_text("Refresh-by: not-a-date\n")
    set_manifest(instance, census={"date": "garbage"})
    out = valid(instance)          # must still return findings JSON, not crash
    assert isinstance(out, list)
```

- [ ] **Step 2: Run, verify FAIL** — `python3 -m pytest tests/test_validate_sweeps.py -v` → the positive tests fail (checks don't exist yet).

- [ ] **Step 3: Implement**

In `templates/hooks/validate.py`, add after the `STAMP` regex:

```python
REFRESH = re.compile(r"Refresh-by: (\d{4}-\d{2}-\d{2})")
CENSUS_STALE_DAYS = 180
```

Add this function above `run()`:

```python
def sweeps(root, m, today):
    """Doctrine-expiry sweeps (P22: structural triggers, never model memory). All soft."""
    out = []
    research = root / "docs" / "RESEARCH.md"
    if research.is_file():
        for d in REFRESH.findall(research.read_text()):
            try:
                if datetime.date.fromisoformat(d) < today:
                    out.append({"check": "research_expired", "level": "soft",
                                "file": "docs/RESEARCH.md", "refresh_by": d})
            except ValueError:
                pass
    census = m.get("census")
    if census:
        try:
            age = (today - datetime.date.fromisoformat(census.get("date", ""))).days
            if age > CENSUS_STALE_DAYS:
                out.append({"check": "census_stale", "level": "soft", "age_days": age})
        except ValueError:
            out.append({"check": "census_stale", "level": "soft", "detail": "unreadable census date"})
    elif m.get("data_paths"):
        out.append({"check": "census_stale", "level": "soft",
                    "detail": "data_paths recorded but no census"})
    last = m.get("metrics", {}).get("last_revalidated")
    days = m.get("cadence", {}).get("proxy_revalidation_days")
    if last and days:
        try:
            age = (today - datetime.date.fromisoformat(last)).days
            if age > days:
                out.append({"check": "proxy_revalidation_due", "level": "soft", "age_days": age})
        except ValueError:
            pass
    return out
```

At the end of `run()`, before `return out`:

```python
    try:
        out += sweeps(root, m, datetime.date.today())
    except Exception:
        pass  # ponytail: sweeps never break the validator's other findings
```

- [ ] **Step 4: Run tests** — new file 7/7 PASS; full suite `python3 -m pytest tests/ -q` green (existing e2e/scaffold tests must be unaffected — legacy manifests are silent by design).

- [ ] **Step 5: Commit** — `git add templates/hooks/validate.py tests/test_validate_sweeps.py && git commit -m "feat(sp3): validate.py sweep checks — research_expired, census_stale, proxy_revalidation_due"`

---

### Task 2: scaffold.py passthrough + revalidation stamps

**Files:**
- Modify: `skills/build/scaffold.py`
- Modify: `tests/test_scaffold.py`

- [ ] **Step 1: Extend failing tests** — add to `tests/test_scaffold.py`:

```python
def test_optional_boundary_fields_pass_through(tmp_path):
    cfg = dict(CFG, census={"date": "2026-07-23", "mcp_servers": ["gmail"]},
               data_paths=[{"need": "chart data", "rung": 4, "why": "no API", "date": "2026-07-23"}],
               boundary={"ask_budget_per_session": 1,
                         "autonomy": {"act": ["log"], "ask": ["restructure"], "never": ["delete archive"]}})
    cfg_file = tmp_path / "cfg2.json"
    cfg_file.write_text(json.dumps(cfg))
    target = tmp_path / "inst2"
    r = subprocess.run([sys.executable, str(REPO / "skills" / "build" / "scaffold.py"),
                        str(cfg_file), str(target)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    m = json.loads((target / "manifest.json").read_text())
    assert m["census"]["mcp_servers"] == ["gmail"]
    assert m["data_paths"][0]["rung"] == 4
    assert m["boundary"]["ask_budget_per_session"] == 1

def test_revalidation_stamps_always_present(tmp_path):
    m = json.loads((scaffold(tmp_path) / "manifest.json").read_text())
    assert m["metrics"]["last_revalidated"] == m["instance"]["created"]
    assert m["cadence"]["proxy_revalidation_days"] == 365
```

Run → FAIL (fields absent).

- [ ] **Step 2: Implement** — in `skills/build/scaffold.py`:
  - In the `manifest = {...}` literal: `"cadence"` gains `"proxy_revalidation_days": 365`; `"metrics"` dict gains `"last_revalidated": today`.
  - After the manifest literal, before writing it:

```python
    for opt in ("census", "data_paths", "boundary"):
        if opt in cfg:
            manifest[opt] = cfg[opt]
```

Also update the module docstring's build-config field list with the three optional fields (one line each, matching its existing terse style).

- [ ] **Step 3: Run** — `python3 -m pytest tests/test_scaffold.py tests/test_validate_sweeps.py -v` all PASS (note: `test_revalidation_stamps_always_present` + Task 1's `proxy_revalidation_due` fresh-stamp path compose: a fresh instance is silent). Full suite green.

- [ ] **Step 4: Commit** — `git add skills/build/scaffold.py tests/test_scaffold.py && git commit -m "feat(sp3): scaffolder passthrough for census/data_paths/boundary + revalidation stamps"`

---

### Task 3: Builder wiring — census, ladder, probes, boundary

**Files:**
- Modify: `skills/build/SKILL.md`
- Modify: `tests/test_skills_exist.py` (build tokens += `["census", "rung", "pass^k", "boundary", "ask_budget"]`)

- [ ] **Step 1: Extend failing test** — append the five tokens to the existing `"build"` list in `tests/test_skills_exist.py`; run → FAIL.

- [ ] **Step 2: Read `skills/build/SKILL.md` end to end**, then insert three blocks (verbatim below) at the named anchors, adjusting ONLY heading level/stage flow if the file's numbering demands it:

**Block A — new stage after Stage 1 (orient/draft), before Stage 2 (goals). Heading: `## Stage 1.5 — Environment census & data paths (P23)`:**

```markdown
Enumerate what THIS machine can actually do, before designing around presence or absence:
list the session's MCP servers/tools (and `claude mcp list` via Bash where available), and
note surfaces (Chrome extension, computer use). Record in the build-config `census` field
(date, mcp_servers, surfaces) — the scaffolder persists it to manifest.json.

For each data need the draft surfaces, walk the data-access ladder and record the rung and
reason in the build-config `data_paths` field:
1 connected MCP/API → 2 connector exists but isn't installed (propose installing — discovery
is manual, there is no registry-search API) → 3 browser automation on the authenticated web
app → 4 screenshot + vision → 5 manual user entry.
Landing below rung 1 is normal — the recorded rung is what lets the governor propose an
upgrade the day a better path appears. Never design around an absence that is five minutes
from fixable: rung 2 beats rung 4.
```

**Block B — new stage directly after Stage 2.5 (research). Heading: `## Stage 2.6 — Capability probes (P17): pass^k, not vibes`:**

```markdown
List every load-bearing assumption of the form "the model can do X reliably" that the design
commits to (parsing a format, grading an answer, extracting from a screenshot...). For each,
run a small probe BEFORE scaffolding: k=5 repeated trials on 2-3 realistic task instances
via cheap subagents. Reliability is pass^k — all trials pass — not pass@k; single-trial
success is a coin-flip threshold, not a guarantee (P17). All-pass → record a decisions[]
entry (grade VERIFIED-probed, date — probes are perishable, the governor re-probes on
failure clusters). Any-fail → redesign: add a checked verifier, move the step below the
autonomy line, or drop the feature. A $0.05 probe now beats a dead instance at review time.
Skip probes only for capabilities the kernel itself already exercises (file edits, event
logging).
```

**Block C — inside the metric-contract stage (Stage 3), after the guardrails are set. Heading: `### The boundary contract (P19)`:**

```markdown
Set, with the user, blast-ordered largest first (build-config `boundary` field):
- **autonomy table** — three lists: `act` (reversible-in-instance: do it, log it), `ask`
  (hard-to-reverse or outward-facing: inhibitive confirm), `never` (irreversible + external:
  never autonomous). Autonomy inversely proportional to irreversibility.
- **ask_budget_per_session** — default 1. Asks are a rationed budget: ask FREQUENCY, not
  per-ask depth, drives abandonment (P19). Every prompt the instance adds must name which
  budget slot it spends.
Enforcement in v1 is instructional + telemetry-audited (overreach events), not hook-gated —
record this as a decisions[] entry graded BET so the governor can revisit it if overreach
tags appear.
```

- [ ] **Step 3: Coherence read** of the edited file (stage numbering, references between stages, Stage 2.6 probes citing Stage 2.5's research output where natural). Run `python3 -m pytest tests/ -q` → green.

- [ ] **Step 4: Commit** — `git add skills/build/SKILL.md tests/test_skills_exist.py && git commit -m "feat(sp3): builder census + data-access ladder + pass^k probes + boundary contract"`

---

### Task 4: Governor wiring — sweeps, failure audit, de-automation + log.md tags

**Files:**
- Modify: `skills/review/SKILL.md`
- Modify: `templates/instance/commands/log.md`
- Modify: `tests/test_skills_exist.py` (review tokens += `["research_expired", "census_stale", "proxy_revalidation", "failure_mode", "de-automat"]`)
- Modify: `tests/test_templates.py` (add: log.md template must contain `failure_mode` and at least the tags `spec`, `verify`, `overreach`)

- [ ] **Step 1: Extend failing tests** (both files) → run → FAIL.

- [ ] **Step 2: Edit `skills/review/SKILL.md`** (read it end to end first):

In **Stage 3 (metrics report)**, append to the existing paragraph:

```markdown
Also report: failure_mode tag frequencies from events since the last review (spec / verify /
context / overreach / tooling / upkeep — P16), and asks-per-session against
manifest.boundary.ask_budget_per_session (P19). An overreach tag is a boundary-contract
violation — always surfaced, never averaged away.
```

In **Stage 4**, add to the HARD RULES block (after the anti-re-litigation rule):

```markdown
- **Sweep findings become proposals, not chores.** Stage 1's validator now emits doctrine
  sweeps (P22 structural triggers): `research_expired` → propose a re-research run via the
  /cairn:research skill for that section (cite the Refresh-by date); `census_stale` → re-run
  the census (session tools + `claude mcp list`), diff against manifest.census, and where a
  recorded data_paths rung can improve ("rung 1 appeared for X; instance is on rung 4"),
  propose the upgrade; `proxy_revalidation_due` → walk each input lever's causal link to the
  north star against P18's four Goodhart mechanisms (regressional noise, extremal breakdown,
  causal validity, adversarial gaming), then stamp manifest.metrics.last_revalidated with
  today's date whatever the outcome — the check is the event, not the change.
- **De-automation rule (P16/P17).** If the same task class carries the same failure_mode tag
  ≥3 times since the last review, propose moving that task below the autonomy line (act →
  ask, or ask → never) or adding a checked verifier — cite the events. Agents rarely
  self-correct (91.49% of resolutions needed explicit user correction); the correction loop
  is the human plus this rule, not model self-review.
```

- [ ] **Step 3: Edit `templates/instance/commands/log.md`** — extend the friction/outcome line so a user can attach a tag:

```markdown
- Something went wrong: `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/cairn_event.py" friction failure_mode=<spec|verify|context|overreach|tooling|upkeep> note="<what happened>"` (spec=did the wrong thing · verify=a check missed it or none ran · context=lost/stale state · overreach=acted past the autonomy line · tooling=data path broke · upkeep=the system demanded too much)
```

(Adjust to the file's existing bullet format; keep the `{{intents}}` template line untouched.)

- [ ] **Step 4: Coherence read + full suite** — `python3 -m pytest tests/ -q` green.

- [ ] **Step 5: Commit** — `git add skills/review/SKILL.md templates/instance/commands/log.md tests/test_skills_exist.py tests/test_templates.py && git commit -m "feat(sp3): governor sweeps, failure audit, de-automation rule + failure_mode tags in /log"`

---

### Task 5: 0.5.0 release chores

**Files:**
- Modify: `.claude-plugin/plugin.json` (0.4.0 → 0.5.0)
- Modify: `CHANGELOG.md`

- [ ] **Step 1:** Bump version. Insert after `# Changelog`:

```markdown
## 0.5.0 — builder/governor wiring (SP3 of the level-zero umbrella)

- **Environment census + data-access ladder** — the builder enumerates this machine's MCP servers/surfaces and records a rung (1 API → 5 manual) with provenance per data need; the governor re-censuses at review and proposes rung upgrades when the environment improves.
- **pass^k capability probes** — every "the model can do X reliably" assumption is probed (k=5 repeated trials) before scaffolding commits to it; results are dated decisions[] entries the governor can re-probe.
- **Doctrine sweeps in the validator** — `research_expired` (RESEARCH.md Refresh-by dates), `census_stale` (>180d), `proxy_revalidation_due` (annual Goodhart re-check of every lever→north-star link, P18/P22). Deterministic detection, human-gated disposition.
- **Failure-mode telemetry + de-automation** — `/log` friction events carry `failure_mode=` tags (spec/verify/context/overreach/tooling/upkeep, P16); same task class + same tag ≥3 since last review → the governor proposes de-automation or a checked verifier.
- **Boundary contract** — instances carry an autonomy table (act/ask/never, graded by irreversibility) and an ask-budget (default 1/session); v1 enforcement is instructional + telemetry-audited, recorded as a BET.

Umbrella: SP1 (0.3.0) research engine · SP2 (0.4.0) doctrine · SP3 (this) wiring · SP4 (/cairn:audit) next.
```

- [ ] **Step 2:** Full suite green; commit — `git add .claude-plugin/plugin.json CHANGELOG.md && git commit -m "feat: 0.5.0 — builder/governor wiring (census, ladder, probes, sweeps, boundary)"`

---

## Verification (after all tasks)

1. `python3 -m pytest tests/ -q` green.
2. End-to-end smoke: scaffold a throwaway instance WITH census/data_paths/boundary in the config; run `validate.py --json` (fresh instance silent); rewrite its docs/RESEARCH.md with an expired Refresh-by and its manifest census date to 200 days ago; re-run validator → exactly `research_expired` + `census_stale` findings.
3. Read build and review SKILL.md end to end once — stage flow coherent, every new block cites its P-refs, no orphaned references.
4. Legacy safety: run validator against a manifest without any new field (conftest MANIFEST shape) → zero sweep findings.
