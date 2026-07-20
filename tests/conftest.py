import json, subprocess, sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parents[1]
HOOKS = REPO / "templates" / "hooks"

MANIFEST = {
    "cairn_version": "0.1.0",
    "instance": {"name": "test-instance", "created": "2026-07-19"},
    "caps": {
        "CLAUDE.md": {"soft": 4096, "hard": 8192},
        "state/HOT.md": {"soft": 6144, "hard": 12288},
        "state/working/*": {"soft": 16384, "hard": 32768}
    },
    "cadence": {"review_days": 30, "min_sessions": 10, "min_days": 28},
    "intents": ["plan", "log", "other"],
    "metrics": {
        "north_star": {"name": "acted_on_plan", "statement": "I act on what the system planned"},
        "inputs": [{"name": "weekly_reviews"}],
        "guardrails": [{"name": "boot_context_bytes", "max": 24000}]
    },
    "triggers": [
        {"template": "gap_nudge", "days": 7},
        {"template": "review_due", "days": 30},
        {"template": "staleness_escalation", "file": "state/HOT.md", "days": 14},
        {"template": "friction_accumulator", "count": 3, "window_days": 14},
        {"template": "suspend_suggestion", "lapse_count": 3}
    ],
    "privacy": {"capture_content": False},
    "decisions": []
}

@pytest.fixture
def instance(tmp_path):
    root = tmp_path / "inst"
    (root / "state" / "working").mkdir(parents=True)
    (root / "telemetry").mkdir()
    (root / ".cairn").mkdir()
    (root / ".claude").mkdir()
    (root / "state" / "archive.jsonl").write_text("")
    (root / "telemetry" / "events.jsonl").write_text("")
    (root / "state" / "HOT.md").write_text("# HOT\nLast reconciled: 2026-07-19\n")
    (root / "CLAUDE.md").write_text("# router\n")
    (root / "manifest.json").write_text(json.dumps(MANIFEST))
    return root

def run_script(script, payload=None, cwd=None, argv=()):
    """Run a templates/hooks script as Claude Code would: JSON on stdin, JSON/text on stdout."""
    return subprocess.run(
        [sys.executable, str(HOOKS / script), *argv],
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True, text=True, cwd=str(cwd) if cwd else None)

def events(root):
    lines = (root / "telemetry" / "events.jsonl").read_text().splitlines()
    return [json.loads(l) for l in lines if l.strip()]
