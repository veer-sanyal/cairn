"""Registry helpers: rebuildable global index at $CAIRN_HOME/registry.json (SP6)."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "templates" / "hooks"))
import cairn_lib
from conftest import MANIFEST


def read_reg(home):
    return json.loads((home / "registry.json").read_text())


def test_upsert_creates_file_and_parents(instance, _cairn_home):
    assert cairn_lib.registry_upsert(instance) is True
    reg = read_reg(_cairn_home)
    entry = reg["instances"][str(instance.resolve())]
    assert reg["version"] == 1
    assert entry["name"] == "test-instance"
    assert entry["cairn_version"] == "0.1.0"
    assert entry["created"] == "2026-07-19"
    # +00:00 offset, never Z — same format as every event (now_iso)
    assert entry["last_session"].endswith("+00:00")


def test_upsert_purpose_falls_back_to_empty_on_pre_sp6_manifest(instance, _cairn_home):
    # conftest MANIFEST carries purpose (post-SP6); strip it to simulate an old instance
    m = json.loads((instance / "manifest.json").read_text())
    m["instance"].pop("purpose", None)
    (instance / "manifest.json").write_text(json.dumps(m))
    cairn_lib.registry_upsert(instance)
    assert read_reg(_cairn_home)["instances"][str(instance.resolve())]["purpose"] == ""


def test_upsert_updates_own_entry_without_touching_others(instance, _cairn_home):
    other = {"name": "other", "purpose": "p", "created": "2026-01-01",
             "last_session": "2026-01-01T00:00:00+00:00", "cairn_version": "0.5.0"}
    (_cairn_home).mkdir(parents=True)
    (_cairn_home / "registry.json").write_text(json.dumps(
        {"version": 1, "instances": {"/elsewhere/other": other}}))
    cairn_lib.registry_upsert(instance)
    reg = read_reg(_cairn_home)
    assert reg["instances"]["/elsewhere/other"] == other
    assert str(instance.resolve()) in reg["instances"]


def test_corrupt_registry_coerced_fresh_not_crash(instance, _cairn_home):
    _cairn_home.mkdir(parents=True)
    (_cairn_home / "registry.json").write_text("{not json")
    assert cairn_lib.registry_upsert(instance) is True
    reg = read_reg(_cairn_home)
    assert list(reg["instances"]) == [str(instance.resolve())]


def test_non_object_registry_coerced_fresh(instance, _cairn_home):
    _cairn_home.mkdir(parents=True)
    (_cairn_home / "registry.json").write_text("5")
    assert cairn_lib.registry_upsert(instance) is True
    assert str(instance.resolve()) in read_reg(_cairn_home)["instances"]


def test_upsert_fail_soft_on_unwritable_home(instance, _cairn_home, monkeypatch):
    # a FILE where the directory should be makes mkdir/replace fail
    _cairn_home.parent.mkdir(parents=True, exist_ok=True)
    _cairn_home.write_text("i am a file, not a dir")
    assert cairn_lib.registry_upsert(instance) is False  # returns, never raises


def test_registry_remove(instance, _cairn_home):
    cairn_lib.registry_upsert(instance)
    assert cairn_lib.registry_remove(str(instance.resolve())) is True
    assert read_reg(_cairn_home)["instances"] == {}


def test_no_temp_files_left_behind(instance, _cairn_home):
    cairn_lib.registry_upsert(instance)
    leftovers = [p for p in _cairn_home.iterdir() if p.name != "registry.json"]
    assert leftovers == []
