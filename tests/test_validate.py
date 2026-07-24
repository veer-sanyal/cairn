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
    s = instance / ".cairn" / "review-in-progress"
    s.write_text("")
    old = time.time() - 25 * 3600
    os.utime(s, (old, old))
    assert any(x["check"] == "stale_sentinel" for x in findings(instance))

def test_binary_byte_in_events_does_not_suppress_findings(instance):
    # a 0x80 byte used to UnicodeDecodeError the jsonl read → blanket except → [] (A1/C1)
    (instance / "state" / "HOT.md").write_text("# no stamp\n")   # hard finding must survive
    (instance / "telemetry" / "events.jsonl").write_bytes(b'{"ok":1}\n\x80garbage\n')
    f = findings(instance)
    assert any(x["check"] == "staleness" and x["level"] == "hard" for x in f)
    # the replaced-garbage line fails json.loads legitimately → surfaces, not vanishes
    assert any(x["check"] == "jsonl_integrity" and x["file"] == "telemetry/events.jsonl" for x in f)

def test_binary_hot_md_does_not_suppress_findings(instance):
    (instance / "state" / "HOT.md").write_bytes(b"\x80\x81 not text\n")
    (instance / "CLAUDE.md").write_text("x" * 9000)              # unrelated hard finding
    f = findings(instance)
    assert any(x["check"] == "size_cap" and x["level"] == "hard" for x in f)
    assert any(x["check"] == "staleness" for x in f)             # no stamp in the garbage

def test_misplaced_top_level_concluded_flagged(instance):
    # a conclude.md edit gone wrong: top-level "concluded" is ignored by every reader (A9)
    m = json.loads((instance / "manifest.json").read_text())
    m["concluded"] = True
    (instance / "manifest.json").write_text(json.dumps(m))
    f = findings(instance)
    assert any(x["check"] == "misplaced_concluded" and x["level"] == "soft" for x in f)

def test_correctly_placed_concluded_not_flagged(instance):
    m = json.loads((instance / "manifest.json").read_text())
    m["instance"]["concluded"] = True
    (instance / "manifest.json").write_text(json.dumps(m))
    assert not any(x["check"] == "misplaced_concluded" for x in findings(instance))

def test_human_output_default(instance):
    (instance / "CLAUDE.md").write_text("x" * 9000)
    r = run_script("validate.py", cwd=instance)
    assert "size_cap" in r.stdout and r.returncode == 0
