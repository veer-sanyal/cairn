import json, datetime
from conftest import run_script

def valid(instance):
    r = run_script("validate.py", argv=["--json"], cwd=instance)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)

def checks(instance, name):
    return [f for f in valid(instance) if f["check"] == name]

def set_manifest(instance, **patch):
    m = json.loads((instance / "manifest.json").read_text())
    m.update(patch)
    (instance / "manifest.json").write_text(json.dumps(m))

def days_ago(n):
    return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()

def test_research_expired(instance):
    (instance / "docs").mkdir()
    (instance / "docs" / "RESEARCH.md").write_text(
        f"## a — researched 2026-01-01\nPerishability: perishable · Refresh-by: {days_ago(10)} · Engine: x\n\n"
        f"## b — researched 2026-01-01\nPerishability: durable · Refresh-by: on contradiction · Engine: x\n\n"
        f"## c — researched 2026-01-01\nPerishability: semi-durable · Refresh-by: {days_ago(-100)} · Engine: x\n")
    found = checks(instance, "research_expired")
    assert len(found) == 1 and found[0]["refresh_by"] == days_ago(10)

def test_no_research_file_is_silent(instance):
    assert checks(instance, "research_expired") == []

def test_census_stale_and_fresh(instance):
    set_manifest(instance, census={"date": days_ago(200), "mcp_servers": []})
    assert len(checks(instance, "census_stale")) == 1
    set_manifest(instance, census={"date": days_ago(10), "mcp_servers": []})
    assert checks(instance, "census_stale") == []

def test_data_paths_without_census_flags(instance):
    set_manifest(instance, data_paths=[{"need": "x", "rung": 4, "why": "y", "date": days_ago(1)}])
    assert len(checks(instance, "census_stale")) == 1

def test_legacy_manifest_silent(instance):
    # conftest MANIFEST has no census/data_paths/last_revalidated: all three sweeps silent
    for name in ["research_expired", "census_stale", "proxy_revalidation_due"]:
        assert checks(instance, name) == [], name

def test_proxy_revalidation_due_and_fresh(instance):
    m = json.loads((instance / "manifest.json").read_text())
    m["metrics"]["last_revalidated"] = days_ago(400)
    m["cadence"]["proxy_revalidation_days"] = 365
    (instance / "manifest.json").write_text(json.dumps(m))
    assert len(checks(instance, "proxy_revalidation_due")) == 1
    m["metrics"]["last_revalidated"] = days_ago(30)
    (instance / "manifest.json").write_text(json.dumps(m))
    assert checks(instance, "proxy_revalidation_due") == []

def test_malformed_dates_never_break_validator(instance):
    (instance / "docs").mkdir()
    (instance / "docs" / "RESEARCH.md").write_text("Refresh-by: not-a-date\n")
    set_manifest(instance, census={"date": "garbage"})
    out = valid(instance)          # must still return findings JSON, not crash
    assert isinstance(out, list)
