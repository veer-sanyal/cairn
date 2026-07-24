import json, subprocess, sys
from pathlib import Path
from conftest import REPO, run_script

CFG = {
    "instance_name": "study-coach", "one_line_purpose": "Keeps my exam prep honest",
    "north_star": {"name": "planned_sessions_done", "statement": "I do the sessions I planned"},
    "inputs": [{"name": "weekly_plan_written"}],
    "guardrails": [{"name": "boot_context_bytes", "max": 24000}],
    "intents": ["plan", "study", "other"],
    "triggers": [{"template": "gap_nudge", "days": 7}, {"template": "review_due", "days": 30}],
    "owner_map": [{"fact": "current plan", "owner": "state/working/plan.md"}],
    "initial_now": "Prep", "initial_next": "First plan", "decisions": []
}

def scaffold(tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps(CFG))
    target = tmp_path / "study-coach"
    r = subprocess.run([sys.executable, str(REPO / "skills" / "build" / "scaffold.py"),
                        str(cfg), str(target)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return target

def test_scaffold_layout(tmp_path):
    t = scaffold(tmp_path)
    for rel in ["CLAUDE.md", "manifest.json", "state/HOT.md", "state/archive.jsonl",
                "telemetry/events.jsonl", ".claude/settings.json",
                ".claude/hooks/session_start.py", ".claude/hooks/cairn_lib.py",
                ".claude/commands/log.md", ".claude/commands/suspend.md",
                ".claude/commands/conclude.md", ".claude/commands/help.md",
                ".claude/commands/research.md",
                "README.md", "docs/MANUAL.md", ".cairn",
                ".cairn/.gitkeep", "state/working/.gitkeep",
                ".claude/hooks/doctrine_write.py",
                ".claude/workflows/deep-research.js"]:
        assert (t / rel).exists(), rel

def test_vendored_research_frames_before_engine(tmp_path):
    # The instance /research command must embed the framing front door and forbid raw launches
    # (framing fires first, engine only if warranted) — the vendored directing-research gate.
    r = (scaffold(tmp_path) / ".claude" / "commands" / "research.md").read_text()
    assert "{{" not in r
    assert "Frame (fires first" in r and "Right-size" in r
    assert "Never launch" in r and "deep-research.js" in r          # no raw launches
    assert "GROUNDING" in r and "doctrine_write.py" in r            # ground + persist

def test_generated_docs_show_metric_tree(tmp_path):
    t = scaffold(tmp_path)
    for doc in ("README.md", "docs/MANUAL.md"):
        text = (t / doc).read_text()
        assert "{{" not in text, f"unrendered placeholder in {doc}"
        assert "planned_sessions_done" in text       # north star name
        assert "weekly_plan_written" in text          # input lever
        assert "boot_context_bytes" in text           # guardrail
        assert "managed-by-cairn" in text             # regeneration provenance

def test_docs_regenerate_but_spare_user_override(tmp_path):
    t = scaffold(tmp_path)
    render = REPO / "skills" / "build" / "render_docs.py"
    manifest = t / "manifest.json"
    # idempotent re-render (the path /cairn:review and /cairn:upgrade use)
    r = subprocess.run([sys.executable, str(render), str(manifest), str(t)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (t / "README.md").read_text().count("planned_sessions_done") >= 1
    # a doc the user made their own (managed header dropped) is never clobbered
    manual = t / "docs" / "MANUAL.md"
    manual.write_text("# my own notes\n")
    subprocess.run([sys.executable, str(render), str(manifest), str(t)],
                   capture_output=True, text=True)
    assert manual.read_text() == "# my own notes\n"

def test_substitution_and_no_leftover_placeholders(tmp_path):
    t = scaffold(tmp_path)
    claude = (t / "CLAUDE.md").read_text()
    assert "study-coach" in claude and "{{" not in claude
    assert "{{" not in (t / "state" / "HOT.md").read_text()
    assert "{{" not in (t / ".claude" / "commands" / "log.md").read_text()

def test_manifest_carries_contract(tmp_path):
    m = json.loads((scaffold(tmp_path) / "manifest.json").read_text())
    assert m["cairn_version"] and m["metrics"]["north_star"]["name"] == "planned_sessions_done"
    assert m["caps"]["CLAUDE.md"]["hard"] == 8192
    assert m["auto_adopt"] == {"armed": False}   # opt-in at build; default disarmed

def test_scaffolded_instance_boots_clean(tmp_path):
    t = scaffold(tmp_path)
    r = run_script("validate.py", cwd=t, argv=["--json"])
    assert json.loads(r.stdout) == []

def test_refuses_nonempty_target(tmp_path):
    t = scaffold(tmp_path)
    cfg = tmp_path / "cfg.json"
    r = subprocess.run([sys.executable, str(REPO / "skills" / "build" / "scaffold.py"),
                        str(cfg), str(t)], capture_output=True, text=True)
    assert r.returncode != 0   # scaffolder is the ONE script allowed to hard-fail: it's plugin-side

def test_optional_boundary_fields_pass_through(tmp_path):
    cfg = dict(CFG, census={"date": "2026-07-23", "mcp_servers": ["gmail"]},
               data_paths=[{"need": "chart data", "rung": 4, "why": "no API", "date": "2026-07-23"}],
               boundary={"ask_budget_per_session": 1,
                         "autonomy": {"act": ["log"], "ask": ["restructure"], "never": ["delete archive"]}})
    cfg_file = tmp_path / "cfg2.json"
    cfg_file.write_text(json.dumps(cfg))
    target = tmp_path / "inst2"
    r = subprocess.run([sys.executable, str(REPO / "skills" / "build" / "scaffold.py"),
                        str(cfg_file), str(target)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    m = json.loads((target / "manifest.json").read_text())
    assert m["census"]["mcp_servers"] == ["gmail"]
    assert m["data_paths"][0]["rung"] == 4
    assert m["boundary"]["ask_budget_per_session"] == 1

def test_revalidation_stamps_always_present(tmp_path):
    m = json.loads((scaffold(tmp_path) / "manifest.json").read_text())
    assert m["metrics"]["last_revalidated"] == m["instance"]["created"]
    assert m["cadence"]["proxy_revalidation_days"] == 365

def test_system_map_rendered(tmp_path):
    t = scaffold(tmp_path)
    text = (t / "docs" / "SYSTEM-MAP.md").read_text()
    assert "{{" not in text
    assert "study-coach" in text
    assert "Last reconciled:" in text
    for fid in ["session-start", "log-event", "guard-write", "review-cycle"]:
        assert f"## Flow: {fid}" in text, fid


# --- edge-case hardening (0.7.1): fail clean & early, never leave a corrupt half-scaffold ---

def _run(cfg, target, tmp_path, name="cfg"):
    cf = tmp_path / f"{name}.json"; cf.write_text(json.dumps(cfg))
    return subprocess.run([sys.executable, str(REPO / "skills" / "build" / "scaffold.py"),
                           str(cf), str(target)], capture_output=True, text=True)

def test_missing_triggers_fails_before_any_write(tmp_path):
    cfg = {k: v for k, v in CFG.items() if k != "triggers"}
    target = tmp_path / "inst"
    r = _run(cfg, target, tmp_path)
    assert r.returncode != 0 and "triggers" in (r.stdout + r.stderr)
    assert not target.exists() or not any(target.iterdir())   # no corrupt residue

def test_north_star_wrong_type_clean_error(tmp_path):
    cfg = dict(CFG, north_star="just a string")
    r = _run(cfg, tmp_path / "inst", tmp_path)
    assert r.returncode != 0 and "Traceback" not in r.stderr

def test_owner_map_missing_key_clean_error(tmp_path):
    cfg = dict(CFG, owner_map=[{"fact": "x"}])   # no 'owner'
    r = _run(cfg, tmp_path / "inst", tmp_path)
    assert r.returncode != 0 and "Traceback" not in r.stderr

def test_target_is_a_file_clean_refusal(tmp_path):
    f = tmp_path / "afile"; f.write_text("i am a file")
    r = _run(CFG, f, tmp_path)
    assert r.returncode != 0 and "Traceback" not in r.stderr

def test_user_content_with_double_braces_still_scaffolds(tmp_path):
    cfg = dict(CFG, one_line_purpose="a tool that renders {{handlebars}} templates")
    target = tmp_path / "inst"
    r = _run(cfg, target, tmp_path)
    assert r.returncode == 0, r.stderr
    assert "{{handlebars}}" in (target / "CLAUDE.md").read_text()   # literal, not an error

# --- SP6 cross-instance registry: purpose in manifest + register at build ---

def test_manifest_carries_purpose(tmp_path):
    m = json.loads((scaffold(tmp_path) / "manifest.json").read_text())
    assert m["instance"]["purpose"] == CFG["one_line_purpose"]

def test_scaffold_registers_instance(tmp_path, _cairn_home):
    t = scaffold(tmp_path)
    reg = json.loads((_cairn_home / "registry.json").read_text())
    assert str(t.resolve()) in reg["instances"]

def test_registry_failure_warns_but_scaffold_succeeds(tmp_path, _cairn_home):
    _cairn_home.parent.mkdir(parents=True, exist_ok=True)
    _cairn_home.write_text("file blocking the dir")
    target = tmp_path / "inst"
    r = _run(CFG, target, tmp_path)
    assert r.returncode == 0, r.stderr
    assert (target / "manifest.json").exists()
    assert "registry" in r.stderr.lower()


def test_user_content_naming_a_real_placeholder_is_preserved(tmp_path):
    # "{{today}}" inside user content must stay the user's literal words (single-pass render)
    cfg = dict(CFG, one_line_purpose="track deadlines using {{today}} as the anchor date")
    target = tmp_path / "inst"
    r = _run(cfg, target, tmp_path)
    assert r.returncode == 0, r.stderr
    assert "{{today}}" in (target / "CLAUDE.md").read_text()
