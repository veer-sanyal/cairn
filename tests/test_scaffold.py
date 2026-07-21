import json, subprocess, sys
from pathlib import Path
from conftest import REPO, run_script

CFG = {
    "instance_name": "study-coach", "one_line_purpose": "Keeps my exam prep honest",
    "north_star": {"name": "planned_sessions_done", "statement": "I do the sessions I planned"},
    "inputs": [{"name": "weekly_plan_written"}],
    "guardrails": [{"name": "boot_context_bytes", "max": 24000}],
    "intents": ["plan", "study", "other"],
    "triggers": [{"template": "gap_nudge", "days": 7}, {"template": "review_due", "days": 30}],
    "owner_map": [{"fact": "current plan", "owner": "state/working/plan.md"}],
    "initial_now": "Prep", "initial_next": "First plan", "decisions": []
}

def scaffold(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps(CFG))
    target = tmp_path / "study-coach"
    r = subprocess.run([sys.executable, str(REPO / "skills" / "build" / "scaffold.py"),
                        str(cfg), str(target)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return target

def test_scaffold_layout(tmp_path):
    t = scaffold(tmp_path)
    for rel in ["CLAUDE.md", "manifest.json", "state/HOT.md", "state/archive.jsonl",
                "telemetry/events.jsonl", ".claude/settings.json",
                ".claude/hooks/session_start.py", ".claude/hooks/cairn_lib.py",
                ".claude/commands/log.md", ".claude/commands/suspend.md",
                ".claude/commands/conclude.md", ".cairn",
                ".cairn/.gitkeep", "state/working/.gitkeep"]:
        assert (t / rel).exists(), rel

def test_substitution_and_no_leftover_placeholders(tmp_path):
    t = scaffold(tmp_path)
    claude = (t / "CLAUDE.md").read_text()
    assert "study-coach" in claude and "{{" not in claude
    assert "{{" not in (t / "state" / "HOT.md").read_text()
    assert "{{" not in (t / ".claude" / "commands" / "log.md").read_text()

def test_manifest_carries_contract(tmp_path):
    m = json.loads((scaffold(tmp_path) / "manifest.json").read_text())
    assert m["cairn_version"] and m["metrics"]["north_star"]["name"] == "planned_sessions_done"
    assert m["caps"]["CLAUDE.md"]["hard"] == 8192
    assert m["auto_adopt"] == {"armed": False}   # opt-in at build; default disarmed

def test_scaffolded_instance_boots_clean(tmp_path):
    t = scaffold(tmp_path)
    r = run_script("validate.py", cwd=t, argv=["--json"])
    assert json.loads(r.stdout) == []

def test_refuses_nonempty_target(tmp_path):
    t = scaffold(tmp_path)
    cfg = tmp_path / "cfg.json"
    r = subprocess.run([sys.executable, str(REPO / "skills" / "build" / "scaffold.py"),
                        str(cfg), str(t)], capture_output=True, text=True)
    assert r.returncode != 0   # scaffolder is the ONE script allowed to hard-fail: it's plugin-side
