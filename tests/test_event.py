from conftest import run_script, events

def test_append_event(instance):
    r = run_script("keel_event.py", cwd=instance,
                   argv=["intent", "intent=plan", "note=starting week"])
    assert r.returncode == 0
    evs = events(instance)
    assert len(evs) == 1
    assert evs[0]["type"] == "intent"
    assert evs[0]["intent"] == "plan"
    assert "ts" in evs[0]

def test_outside_instance_is_noop(tmp_path):
    r = run_script("keel_event.py", cwd=tmp_path, argv=["intent", "intent=plan"])
    assert r.returncode == 0          # fail-soft: never nonzero
    assert not (tmp_path / "telemetry").exists()

def test_bad_args_fail_soft(instance):
    r = run_script("keel_event.py", cwd=instance, argv=[])
    assert r.returncode == 0
