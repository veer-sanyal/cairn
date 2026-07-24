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

def test_annual_ceiling_fires_on_old_durable_entry(instance):
    (instance / "docs").mkdir()
    (instance / "docs" / "RESEARCH.md").write_text(
        f"## x — researched {days_ago(400)}\n"
        f"Perishability: durable · Refresh-by: on contradiction · Engine: x\n")
    assert len(checks(instance, "research_annual_ceiling")) == 1
    assert checks(instance, "research_expired") == []

def test_annual_ceiling_silent_on_recent(instance):
    (instance / "docs").mkdir()
    (instance / "docs" / "RESEARCH.md").write_text(
        f"## x — researched {days_ago(100)}\n"
        f"Perishability: durable · Refresh-by: on contradiction · Engine: x\n")
    assert checks(instance, "research_annual_ceiling") == []

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

def test_system_map_missing_is_silent(instance):
    assert checks(instance, "system_map") == []

def test_system_map_stale_and_fresh(instance):
    (instance / "docs").mkdir(exist_ok=True)
    smap = instance / "docs" / "SYSTEM-MAP.md"
    smap.write_text(f"# map\n\nLast reconciled: {days_ago(100)}\n")
    assert len(checks(instance, "system_map")) == 1          # 100d > 2*30d review cadence
    smap.write_text(f"# map\n\nLast reconciled: {days_ago(10)}\n")
    assert checks(instance, "system_map") == []

def test_system_map_no_stamp_flags(instance):
    (instance / "docs").mkdir(exist_ok=True)
    (instance / "docs" / "SYSTEM-MAP.md").write_text("# map, no stamp\n")
    assert len(checks(instance, "system_map")) == 1


# --- edge-case hardening (0.7.1): one malformed field must never suppress other findings ---

def test_malformed_census_does_not_suppress_other_sweeps(instance):
    (instance / "docs").mkdir(exist_ok=True)
    (instance / "docs" / "RESEARCH.md").write_text(
        f"## a — researched 2026-01-01\nPerishability: perishable · Refresh-by: {days_ago(10)} · Engine: x\n")
    set_manifest(instance, census=["gmail"])            # wrong type: list, not dict
    names = {f["check"] for f in valid(instance)}
    assert "research_expired" in names                  # NOT swallowed by the census crash
    assert "census_stale" in names                      # malformed census surfaced, not silent

def test_census_date_wrong_type_is_contained(instance):
    set_manifest(instance, census={"date": 20260101})   # int, not an iso string
    assert len(checks(instance, "census_stale")) == 1   # diagnostic, no crash/suppression

def test_metrics_not_a_dict_does_not_crash(instance):
    (instance / "docs").mkdir(exist_ok=True)
    (instance / "docs" / "RESEARCH.md").write_text(
        f"## a — researched 2026-01-01\nPerishability: x · Refresh-by: {days_ago(5)} · Engine: x\n")
    set_manifest(instance, metrics=["oops"])            # wrong type
    assert "research_expired" in {f["check"] for f in valid(instance)}

def test_hot_md_bad_date_does_not_suppress_findings(instance):
    (instance / "state" / "HOT.md").write_text("Last reconciled: 2026-02-30\n")  # impossible date
    assert "staleness" in {f["check"] for f in valid(instance)}                   # surfaced, not a crash
    (instance / "telemetry" / "events.jsonl").write_text("{bad json\n")
    assert "jsonl_integrity" in {f["check"] for f in valid(instance)}            # hard finding survives

def test_degenerate_cadence_review_days_zero(instance):
    (instance / "docs").mkdir(exist_ok=True)
    (instance / "docs" / "SYSTEM-MAP.md").write_text(f"Last reconciled: {days_ago(1)}\n")
    set_manifest(instance, cadence={"review_days": 0})   # 2*0=0 would flag a 1-day-old map
    assert checks(instance, "system_map") == []          # falls back to sane default

def test_degenerate_proxy_days_non_positive(instance):
    set_manifest(instance, metrics={"last_revalidated": days_ago(1)},
                 cadence={"review_days": 30, "proxy_revalidation_days": -5})
    assert checks(instance, "proxy_revalidation_due") == []   # non-positive = don't check
