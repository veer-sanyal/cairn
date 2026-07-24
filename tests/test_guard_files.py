import json
from conftest import run_script

def hook(instance, tool, path, content="x"):
    return run_script("guard_files.py", cwd=instance, payload={
        "hook_event_name": "PreToolUse", "cwd": str(instance),
        "tool_name": tool, "tool_input": {"file_path": str(instance / path), "content": content}})

def denied(r):
    if not r.stdout.strip():
        return False
    return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"

def test_archive_write_denied(instance):
    assert denied(hook(instance, "Write", "state/archive.jsonl"))

def test_archive_edit_denied(instance):
    assert denied(hook(instance, "Edit", "state/archive.jsonl"))

def test_working_edit_allowed(instance):
    (instance / "state/working/notes.md").write_text("a")
    assert not denied(hook(instance, "Edit", "state/working/notes.md"))

def test_working_overwrite_denied_without_sentinel(instance):
    (instance / "state/working/notes.md").write_text("a")
    assert denied(hook(instance, "Write", "state/working/notes.md"))

def test_working_overwrite_allowed_with_sentinel(instance):
    (instance / "state/working/notes.md").write_text("a")
    (instance / ".cairn/review-in-progress").write_text("")
    assert not denied(hook(instance, "Write", "state/working/notes.md"))

def test_working_new_file_write_allowed(instance):
    assert not denied(hook(instance, "Write", "state/working/new.md"))

def test_hard_cap_projected_write_denied(instance):
    assert denied(hook(instance, "Write", "CLAUDE.md", content="x" * 9000))

def test_relative_archive_path_denied(instance, tmp_path):
    # a relative file_path resolves against the payload cwd, not the process cwd —
    # the process cwd is the harness's, which used to silently allow (A6)
    r = run_script("guard_files.py", cwd=tmp_path, payload={
        "hook_event_name": "PreToolUse", "cwd": str(instance),
        "tool_name": "Write", "tool_input": {"file_path": "state/archive.jsonl", "content": "x"}})
    assert denied(r)

def test_outside_instance_allowed(tmp_path):
    r = run_script("guard_files.py", cwd=tmp_path, payload={
        "tool_name": "Write", "cwd": str(tmp_path),
        "tool_input": {"file_path": str(tmp_path / "anything.md"), "content": "x"}})
    assert r.returncode == 0 and not r.stdout.strip()

def test_garbage_stdin_fail_soft(instance):
    import subprocess, sys
    from conftest import HOOKS
    r = subprocess.run([sys.executable, str(HOOKS / "guard_files.py")],
                       input="not json", capture_output=True, text=True, cwd=str(instance))
    assert r.returncode == 0
