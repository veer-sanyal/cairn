from conftest import run_script, events

def test_end_event_with_duration(instance):
    run_script("session_start.py", cwd=instance,
               payload={"hook_event_name": "SessionStart", "cwd": str(instance), "session_id": "s1"})
    r = run_script("session_end.py", cwd=instance,
                   payload={"hook_event_name": "SessionEnd", "cwd": str(instance),
                            "session_id": "s1", "reason": "exit"})
    assert r.returncode == 0
    ends = [e for e in events(instance) if e["type"] == "session" and e["phase"] == "end"]
    assert len(ends) == 1 and ends[0]["duration_s"] >= 0 and ends[0]["session_id"] == "s1"

def test_end_without_start_fail_soft(instance):
    r = run_script("session_end.py", cwd=instance,
                   payload={"hook_event_name": "SessionEnd", "cwd": str(instance), "session_id": "sX"})
    assert r.returncode == 0
