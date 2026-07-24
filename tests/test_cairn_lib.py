import json, sys
from conftest import REPO
sys.path.insert(0, str(REPO / "templates" / "hooks"))
import cairn_lib

def test_find_root_skips_scalar_manifest(tmp_path):
    # an inner dir with a scalar manifest.json must not abort the walk to a valid outer root
    outer = tmp_path / "outer"; outer.mkdir()
    (outer / "manifest.json").write_text(json.dumps({"cairn_version": "0.7.1"}))
    inner = outer / "inner"; inner.mkdir()
    (inner / "manifest.json").write_text("5")   # scalar JSON — 'in' would raise TypeError
    assert cairn_lib.find_root(inner) == outer

def test_manifest_returns_dict_for_scalar(tmp_path):
    (tmp_path / "manifest.json").write_text("true")
    assert cairn_lib.manifest(tmp_path) == {}

def test_parse_helpers():
    assert cairn_lib.parse_date("2026-07-23") is not None
    assert cairn_lib.parse_date("2026-02-30") is None      # impossible date
    assert cairn_lib.parse_date(None) is None and cairn_lib.parse_date(5) is None
    ts = cairn_lib.parse_ts("2026-07-01T10:00:00")         # naive → normalized aware
    assert ts is not None and ts.tzinfo is not None
    assert cairn_lib.parse_ts("garbage") is None and cairn_lib.parse_ts(None) is None
    assert cairn_lib.pos_int(30) == 30
    assert cairn_lib.pos_int(True) is None                  # bool excluded
    assert cairn_lib.pos_int(0) is None and cairn_lib.pos_int(-5) is None and cairn_lib.pos_int("30") is None
