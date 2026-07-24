import json
from pathlib import Path
from conftest import REPO

T = REPO / "templates" / "instance"

def test_templates_exist_and_are_wired():
    settings = json.loads((T / "settings.json.tmpl").read_text())
    events = settings["hooks"]
    assert set(events) == {"SessionStart", "SessionEnd", "PreToolUse"}
    matchers = [h.get("matcher") for h in events["PreToolUse"]]
    assert "Write|Edit" in matchers and "Bash" in matchers
    for cmd in ["log.md", "suspend.md", "conclude.md"]:
        assert (T / "commands" / cmd).is_file()
    assert "{{instance_name}}" in (T / "CLAUDE.md.tmpl").read_text()
    assert "Last reconciled:" in (T / "HOT.md.tmpl").read_text()

def test_claude_tmpl_has_checkpoint_after_error_rule():
    text = (T / "CLAUDE.md.tmpl").read_text()
    assert "failure_mode" in text
    assert "P16" in text

def test_command_templates_carry_managed_header():
    for cmd in ["log.md", "suspend.md", "conclude.md"]:
        assert "managed-by-cairn" in (T / "commands" / cmd).read_text()

def test_log_template_documents_failure_mode_tags():
    text = (T / "commands" / "log.md").read_text()
    assert "failure_mode" in text
    for tag in ["spec", "verify", "overreach"]:
        assert tag in text
