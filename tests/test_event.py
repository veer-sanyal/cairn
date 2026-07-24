from conftest import run_script, events

def test_append_event(instance):
    r = run_script("cairn_event.py", cwd=instance,
                   argv=["intent", "intent=plan", "note=starting week"])
    assert r.returncode == 0
    evs = events(instance)
    assert len(evs) == 1
    assert evs[0]["type"] == "intent"
    assert evs[0]["intent"] == "plan"
    assert "ts" in evs[0]

def test_outside_cwd_falls_back_to_script_location(instance, tmp_path):
    # B2: invoked by absolute path from a cwd OUTSIDE the instance, the script
    # locates its instance from its own path (<root>/.claude/hooks/cairn_event.py)
    import shutil, subprocess, sys
    from conftest import HOOKS
    hooks = instance / ".claude" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    shutil.copy(HOOKS / "cairn_event.py", hooks / "cairn_event.py")
    shutil.copy(HOOKS / "cairn_lib.py", hooks / "cairn_lib.py")
    r = subprocess.run([sys.executable, str(hooks / "cairn_event.py"),
                        "intent", "intent=plan"],
                       capture_output=True, text=True, cwd=str(tmp_path))
    assert r.returncode == 0
    evs = events(instance)
    assert len(evs) == 1 and evs[0]["type"] == "intent"

def test_outside_instance_is_noop(tmp_path):
    r = run_script("cairn_event.py", cwd=tmp_path, argv=["intent", "intent=plan"])
    assert r.returncode == 0          # fail-soft: never nonzero
    assert not (tmp_path / "telemetry").exists()

def test_bad_args_fail_soft(instance):
    r = run_script("cairn_event.py", cwd=instance, argv=[])
    assert r.returncode == 0
