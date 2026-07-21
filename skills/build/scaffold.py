#!/usr/bin/env python3
"""Deterministic cairn instance scaffolder. Usage: scaffold.py <build-config.json> <target-dir>
Plugin-side (not an instance hook): hard failures are correct here.

Build-config JSON fields (all required unless noted):
  instance_name      str   e.g. "study-coach"
  one_line_purpose   str
  north_star         {"name": str, "statement": str}  # user's own words
  intents            [str, ...]
  triggers           [{"template": str, ...params}, ...]
  owner_map          [{"fact": str, "owner": str}, ...]  (optional)
  inputs             [{"name": str}, ...]                (optional)
  guardrails         [{"name": str, "max": num}, ...]    (optional)
  decisions          [{"id","decision","principle","grade","blast","one_way"}, ...] (optional)
                     blast: "low"|"med"|"high" (what else changes if this flips);
                     one_way: bool (irreversible within one review period?).
                     Ids are immutable: the governor supersedes by appending a NEW entry
                     with "supersedes" and annotating the old one with "status":
                     "superseded" + "superseded_by" + "superseded_on" — never renumber,
                     reuse, delete, or rewrite an entry in place. Optional "dissent":
                     "<concern> — user proceeded <date>" when the call was made over a
                     flagged second opinion (the trail survives without re-arguing).
  auto_adopt         bool (optional, default false) — arm the governor's bounded
                     auto-adopt lane (low-blast, two-way, VERIFIED-backed proposals
                     apply with a 7-day boot-visible revert window)
  initial_now        str  (optional)
  initial_next       str  (optional)
"""
import json, sys, shutil, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
T = REPO / "templates"
CAIRN_VERSION = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text())["version"]
CAPS = {"CLAUDE.md": {"soft": 4096, "hard": 8192},
        "state/HOT.md": {"soft": 6144, "hard": 12288},
        "state/working/*": {"soft": 16384, "hard": 32768}}

def render(tmpl, subs):
    out = tmpl
    for k, v in subs.items():
        out = out.replace("{{" + k + "}}", str(v))
    if "{{" in out:
        sys.exit(f"unrendered placeholder remains: {out[out.index('{{'):out.index('{{')+40]}")
    return out

def main():
    cfg = json.loads(Path(sys.argv[1]).read_text())
    target = Path(sys.argv[2])
    if target.exists() and any(target.iterdir()):
        sys.exit(f"target {target} exists and is not empty — refusing (no silent overwrite)")
    today = datetime.date.today().isoformat()
    subs = {
        "cairn_version": CAIRN_VERSION, "instance_name": cfg["instance_name"],
        "one_line_purpose": cfg["one_line_purpose"], "today": today,
        "north_star_name": cfg["north_star"]["name"],
        "north_star_statement": cfg["north_star"]["statement"],
        "initial_now": cfg.get("initial_now", ""), "initial_next": cfg.get("initial_next", ""),
        "intents": ", ".join(cfg["intents"]),
        "owner_map": "\n".join(f"- {o['fact']} → `{o['owner']}`" for o in cfg.get("owner_map", [])),
    }
    (target / "state" / "working").mkdir(parents=True)
    (target / "telemetry").mkdir()
    (target / ".cairn").mkdir()
    (target / ".claude" / "hooks").mkdir(parents=True)
    (target / ".claude" / "commands").mkdir(parents=True)
    # empty dirs don't survive git clone; review's sentinel touch needs .cairn/ to exist
    (target / ".cairn" / ".gitkeep").write_text("")
    (target / "state" / "working" / ".gitkeep").write_text("")
    (target / "state" / "archive.jsonl").write_text("")
    (target / "telemetry" / "events.jsonl").write_text("")
    (target / "CLAUDE.md").write_text(render((T / "instance" / "CLAUDE.md.tmpl").read_text(), subs))
    (target / "state" / "HOT.md").write_text(render((T / "instance" / "HOT.md.tmpl").read_text(), subs))
    (target / ".claude" / "settings.json").write_text(
        render((T / "instance" / "settings.json.tmpl").read_text(), subs))
    for cmd in (T / "instance" / "commands").glob("*.md"):
        (target / ".claude" / "commands" / cmd.name).write_text(render(cmd.read_text(), subs))
    for hook in (T / "hooks").glob("*.py"):
        shutil.copy(hook, target / ".claude" / "hooks" / hook.name)
    manifest = {
        "cairn_version": CAIRN_VERSION,
        "instance": {"name": cfg["instance_name"], "created": today},
        "caps": CAPS,
        "cadence": {"review_days": 30, "min_sessions": 10, "min_days": 28},
        "intents": cfg["intents"],
        "metrics": {"north_star": cfg["north_star"], "inputs": cfg.get("inputs", []),
                    "guardrails": cfg.get("guardrails", [])},
        "triggers": cfg["triggers"],
        "privacy": {"capture_content": False},
        "auto_adopt": {"armed": bool(cfg.get("auto_adopt", False))},
        "decisions": cfg.get("decisions", []),
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"scaffolded {cfg['instance_name']} at {target}")

if __name__ == "__main__":
    main()
