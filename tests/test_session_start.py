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

def test_refire_same_session_id_no_false_lapse(instance):
    boot(instance)                      # first boot, session s2
    boot(instance)                      # re-fire, same session_id s2 (resume/compact)
    from conftest import events
    assert not any(e["type"] == "lapse" for e in events(instance))

def test_naive_timestamp_does_not_kill_banner(instance):
    import json
    with open(instance / "telemetry" / "events.jsonl", "a") as f:
        f.write(json.dumps({"ts": "2026-07-01T10:00:00", "type": "session",
                            "phase": "start", "session_id": "s0"}) + "\n")
    out = boot(instance)
    assert ctx(out)                     # banner still emitted
