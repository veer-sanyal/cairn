import json, subprocess, sys
from pathlib import Path
from conftest import REPO
from test_scaffold import scaffold, CFG

def hook(t, script, payload):
    return subprocess.run([sys.executable, str(t / ".claude" / "hooks" / script)],
                         input=json.dumps(payload), capture_output=True, text=True, cwd=str(t))

def test_full_session_lifecycle(tmp_path):
    t = scaffold(tmp_path)
    # session 1: boot, work, log, end
    r = hook(t, "session_start.py", {"cwd": str(t), "session_id": "s1"})
    assert "new instance" in r.stdout.lower()
    assert hook(t, "guard_files.py", {"cwd": str(t), "tool_name": "Write",
        "tool_input": {"file_path": str(t / "state/archive.jsonl"), "content": "x"}}
        ).stdout.count("deny") == 1
    subprocess.run([sys.executable, str(t / ".claude/hooks/keel_event.py"),
                    "intent", "intent=plan"], cwd=str(t))
    hook(t, "session_end.py", {"cwd": str(t), "session_id": "s1", "reason": "exit"})
    # session 2: boot again — no lapse (s1 had an intent), validator clean
    r2 = hook(t, "session_start.py", {"cwd": str(t), "session_id": "s2"})
    evs = [json.loads(l) for l in (t / "telemetry/events.jsonl").read_text().splitlines()]
    assert not any(e["type"] == "lapse" for e in evs)
    v = subprocess.run([sys.executable, str(t / ".claude/hooks/validate.py"), "--json"],
                       capture_output=True, text=True, cwd=str(t))
    assert json.loads(v.stdout) == []
