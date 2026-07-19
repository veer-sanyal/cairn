import json
from conftest import run_script

def hook(instance, cmd):
    return run_script("guard_bash.py", cwd=instance, payload={
        "hook_event_name": "PreToolUse", "cwd": str(instance),
        "tool_name": "Bash", "tool_input": {"command": cmd}})

def denied(r):
    return bool(r.stdout.strip()) and \
        json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"

def test_rm_working_denied(instance):
    assert denied(hook(instance, "rm state/working/notes.md"))

def test_rm_archive_denied(instance):
    assert denied(hook(instance, "rm -f state/archive.jsonl"))

def test_truncate_archive_denied(instance):
    assert denied(hook(instance, "echo hi > state/archive.jsonl"))

def test_append_archive_allowed(instance):
    assert not denied(hook(instance, 'echo "{}" >> state/archive.jsonl'))

def test_append_no_space_allowed(instance):
    assert not denied(hook(instance, 'echo "{}" >>state/archive.jsonl'))

def test_rm_unrelated_then_read_allowed(instance):
    assert not denied(hook(instance, "rm /tmp/junk && cat state/archive.jsonl"))

def test_rm_chained_still_denied_when_targeting_protected(instance):
    assert denied(hook(instance, "cd . && rm state/working/notes.md"))

def test_ordinary_command_allowed(instance):
    assert not denied(hook(instance, "git status"))

def test_outside_instance_allowed(tmp_path):
    r = run_script("guard_bash.py", cwd=tmp_path, payload={
        "tool_name": "Bash", "cwd": str(tmp_path),
        "tool_input": {"command": "rm state/archive.jsonl"}})
    assert not denied(r)
