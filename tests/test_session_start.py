import json, datetime
from conftest import run_script, events
from cairn_helpers_for_tests import seed_event  # defined in step 2

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
        seed_event(instance, days_ago=d, type="lapse", cause="skipped")
    seed_event(instance, days_ago=9, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert "/suspend" in ctx(out)

def test_untyped_lapses_do_not_trigger_suspend(instance):
    for d in (30, 20, 10):
        seed_event(instance, days_ago=d, type="lapse", cause="untyped")
    seed_event(instance, days_ago=9, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert "/suspend" not in ctx(out)

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

def test_guardrail_regression_metric_flagged(instance):
    import json
    m = json.loads((instance / "manifest.json").read_text())
    m["metrics"]["guardrails"].append({"name": "ceremony_minutes", "max": 10})
    (instance / "manifest.json").write_text(json.dumps(m))
    seed_event(instance, days_ago=1, type="session", phase="start", session_id="s1")
    seed_event(instance, days_ago=1, type="intent", intent="plan", session_id="s1")
    seed_event(instance, days_ago=0, type="metric", name="ceremony_minutes", value="45")
    out = boot(instance)
    assert "guardrail regression: ceremony_minutes" in ctx(out)

def test_no_guardrail_flag_when_within_max(instance):
    out = boot(instance)   # fresh instance: tiny resident files, no metric events
    assert "guardrail regression" not in ctx(out)

def _iso(days_from_now):
    return (datetime.date.today() + datetime.timedelta(days=days_from_now)).isoformat()

def test_auto_adopt_in_window_named_at_boot(instance):
    seed_event(instance, days_ago=1, type="proposal", id="7", status="auto_adopted",
               blast="low", door="two-way", revert_until=_iso(6))
    seed_event(instance, days_ago=1, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert "auto-adopted #7" in ctx(out) and "revert" in ctx(out)

def test_auto_adopt_silent_after_window_closes(instance):
    seed_event(instance, days_ago=10, type="proposal", id="7", status="auto_adopted",
               blast="low", door="two-way", revert_until=_iso(-3))
    seed_event(instance, days_ago=1, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert "auto-adopted" not in ctx(out)

def test_auto_adopt_silent_after_revert(instance):
    seed_event(instance, days_ago=2, type="proposal", id="7", status="auto_adopted",
               blast="low", door="two-way", revert_until=_iso(5))
    seed_event(instance, days_ago=1, type="proposal", id="7", status="reverted_merits")
    seed_event(instance, days_ago=1, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert "auto-adopted" not in ctx(out)


def test_malformed_ts_does_not_blank_banner(instance):
    # a valid-JSON event with a garbage ts must not suppress the whole banner (0.7.1 harden)
    with open(instance / "telemetry" / "events.jsonl", "a") as f:
        f.write(json.dumps({"ts": "not-a-timestamp", "type": "session",
                            "phase": "start", "session_id": "s0"}) + "\n")
    seed_event(instance, days_ago=9, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert ctx(out)                       # banner present, not blanked by the bad row
    assert "gap" in ctx(out).lower()      # the good event's nudge still computed


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


def test_malformed_triggers_type_does_not_blank_banner(instance):
    # triggers as a dict (hand-edited manifest) must not AttributeError away the banner
    m = json.loads((instance / "manifest.json").read_text())
    m["triggers"] = {"foo": "bar"}
    (instance / "manifest.json").write_text(json.dumps(m))
    seed_event(instance, days_ago=2, type="session", phase="start", session_id="s1")
    out = boot(instance)
    assert ctx(out)   # banner present despite malformed triggers
