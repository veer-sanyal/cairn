import subprocess, sys
from pathlib import Path
from conftest import REPO

MERGE = REPO / "skills" / "upgrade" / "merge.py"

def run_merge(src, dst):
    return subprocess.run([sys.executable, str(MERGE), str(src), str(dst)],
                          capture_output=True, text=True)

def managed(version, body="body"):
    return f"<!-- managed-by-cairn: {version} -->\n{body}\n"

def test_unmodified_managed_file_replaced(tmp_path):
    (tmp_path / "new.md").write_text(managed("0.2.0", "new content"))
    (tmp_path / "inst.md").write_text(managed("0.1.0", "old content"))
    # simulate: the shipped 0.1.0 template is identical to what's installed → replace
    (tmp_path / "orig.md").write_text(managed("0.1.0", "old content"))
    r = subprocess.run([sys.executable, str(MERGE), str(tmp_path / "new.md"),
                        str(tmp_path / "inst.md"), "--original", str(tmp_path / "orig.md")],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "new content" in (tmp_path / "inst.md").read_text()

def test_user_modified_file_gets_cairn_new(tmp_path):
    (tmp_path / "new.md").write_text(managed("0.2.0", "new content"))
    (tmp_path / "inst.md").write_text(managed("0.1.0", "old content\nUSER EDIT"))
    (tmp_path / "orig.md").write_text(managed("0.1.0", "old content"))
    subprocess.run([sys.executable, str(MERGE), str(tmp_path / "new.md"),
                    str(tmp_path / "inst.md"), "--original", str(tmp_path / "orig.md")])
    assert "USER EDIT" in (tmp_path / "inst.md").read_text()          # never overwritten
    assert (tmp_path / "inst.md.cairn-new").exists()                    # lands alongside

def test_identical_managed_file_noop(tmp_path):
    (tmp_path / "new.md").write_text(managed("0.2.0", "same"))
    (tmp_path / "inst.md").write_text(managed("0.2.0", "same"))
    r = run_merge(tmp_path / "new.md", tmp_path / "inst.md")
    assert "identical" in r.stdout
    assert not (tmp_path / "inst.md.cairn-new").exists()

def test_unmanaged_file_untouched(tmp_path):
    (tmp_path / "new.md").write_text(managed("0.2.0"))
    (tmp_path / "inst.md").write_text("no header — user's own file")
    r = run_merge(tmp_path / "new.md", tmp_path / "inst.md")
    assert "user's own file" in (tmp_path / "inst.md").read_text()
    assert not (tmp_path / "inst.md.cairn-new").exists()
