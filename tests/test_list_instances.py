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
