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
