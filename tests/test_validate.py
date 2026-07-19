import json, os, time
from conftest import run_script

def findings(instance):
    r = run_script("validate.py", cwd=instance, argv=["--json"])
    assert r.returncode == 0
    return json.loads(r.stdout)

def test_clean_instance_no_findings(instance):
    assert findings(instance) == []

def test_hard_cap_violation(instance):
    (instance / "CLAUDE.md").write_text("x" * 9000)
    f = findings(instance)
    assert any(x["check"] == "size_cap" and x["level"] == "hard" for x in f)

def test_missing_staleness_stamp(instance):
    (instance / "state" / "HOT.md").write_text("# no stamp\n")
    assert any(x["check"] == "staleness" for x in findings(instance))

def test_corrupt_archive_line(instance):
    (instance / "state" / "archive.jsonl").write_text('{"ok":1}\nnot json\n')
    assert any(x["check"] == "jsonl_integrity" for x in findings(instance))

def test_stale_sentinel(instance):
    s = instance / ".keel" / "review-in-progress"
    s.write_text("")
    old = time.time() - 25 * 3600
    os.utime(s, (old, old))
    assert any(x["check"] == "stale_sentinel" for x in findings(instance))

def test_human_output_default(instance):
    (instance / "CLAUDE.md").write_text("x" * 9000)
    r = run_script("validate.py", cwd=instance)
    assert "size_cap" in r.stdout and r.returncode == 0
