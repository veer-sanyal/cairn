import json, datetime
from conftest import run_script, events
from keel_helpers_for_tests import seed_event  # defined in step 2

def boot(instance):
    r = run_script("session_start.py", cwd=instance, payload={
        "hook_event_name": "SessionStart", "cwd": str(instance), "session_id": "s2"})
    assert r.returncode == 0
    return json.loads(r.stdout) if r.stdout.strip() else {}

def ctx(out):
    return out.get("hookSpecificOutput", {}).get("additionalContext", "")

def test_session_event_written_with_boot_cost(instance):
    boot(instance)
    ev = [e for e in events(instance) if e["type"] == "session" and e["phase"] == "start"]
    assert len(ev) == 1 and ev[0]["boot_context_est_tokens"] > 0

def test_gap_lookback_flags_empty_previous_session(instance):
    seed_event(instance, days_ago=2, type="session", phase="start", session_id="s1")
    seed_event(instance, days_ago=2, type="session", phase="end", session_id="s1")
    boot(instance)
    assert any(e["type"] == "lapse" and e["cause"] == "untyped" for e in events(instance))

def test_no_lapse_when_previous_session_had_intent(instance):
    seed_event(instance, days_ago=2, type="session", phase="start", session_id="s1")
    seed_event(instance, days_ago=2, type="intent", intent="plan", session_id="s1")
    boot(instance)
    assert not any(e["type"] == "lapse" for e in events(instance))

def test_gap_nudge_fires_after_threshold(instance):
    seed_event(instance, days_ago=9, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert "gap" in ctx(out).lower()

def test_new_instance_banner(instance):
    out = boot(instance)   # no prior events at all
    assert "new instance" in ctx(out).lower()

def test_suspend_suggestion_after_lapses(instance):
    for d in (30, 20, 10):
        seed_event(instance, days_ago=d, type="lapse", cause="untyped")
    seed_event(instance, days_ago=9, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert "/suspend" in ctx(out)
