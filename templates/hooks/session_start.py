#!/usr/bin/env python3
"""SessionStart: session event + gap look-back + banner from manifest trigger rules."""
import json, sys, os, datetime, subprocess
from pathlib import Path
from keel_lib import find_root, manifest, append_event

def load_events(root):
    p = Path(root) / "telemetry" / "events.jsonl"
    if not p.is_file():
        return []
    out = []
    for line in p.read_text().splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out

def days_since(ts):
    t = datetime.datetime.fromisoformat(ts)
    return (datetime.datetime.now(datetime.timezone.utc) - t).days

def trig(m, name):
    return next((t for t in m.get("triggers", []) if t.get("template") == name), None)

def main():
    h = json.load(sys.stdin)
    root = find_root(h.get("cwd") or os.getcwd())
    if not root:
        return
    m = manifest(root)
    evs = load_events(root)
    lines = []

    # 1. session start event + boot-cost estimate (resident bytes / 4)
    resident = sum((root / f).stat().st_size for f in ["CLAUDE.md", "state/HOT.md"] if (root / f).is_file())
    append_event(root, "session", phase="start",
                 session_id=h.get("session_id", ""), boot_context_est_tokens=resident // 4)

    if not evs:
        lines.append(f"New instance '{m.get('instance', {}).get('name', '?')}' — no history yet. "
                     "Reviews unlock after the minimum telemetry window (manifest cadence).")
    else:
        # 2. gap look-back: last session with no non-session events => untyped lapse
        sessions = [e for e in evs if e["type"] == "session" and e.get("phase") == "start"]
        if sessions:
            last_id = sessions[-1].get("session_id")
            worked = any(e for e in evs if e.get("session_id") == last_id and e["type"] != "session")
            if not worked:
                append_event(root, "lapse", cause="untyped", about_session=last_id)
                lines.append("Previous session logged no intent/outcome — cause unknown "
                             "(forgot / upkeep / skipped?). Worth typing it via /log.")
        # 3. trigger rules (welcome-back tone, never guilt — spec §3.3)
        t = trig(m, "gap_nudge")
        if t and sessions and days_since(sessions[-1]["ts"]) >= t.get("days", 7):
            lines.append(f"Welcome back — {days_since(sessions[-1]['ts'])}-day gap since last session. "
                         "Here's where things stand (see HOT.md).")
        t = trig(m, "review_due")
        reviews = [e for e in evs if e["type"] == "proposal"]
        anchor = reviews[-1]["ts"] if reviews else evs[0]["ts"]
        if t and days_since(anchor) >= t.get("days", 30):
            lines.append("A review is due — run /keel:review when convenient.")
        t = trig(m, "friction_accumulator")
        if t:
            recent = [e for e in evs if e["type"] == "outcome" and e.get("outcome") == "friction"
                      and days_since(e["ts"]) <= t.get("window_days", 14)]
            if len(recent) >= t.get("count", 3):
                lines.append(f"{len(recent)} friction events in {t.get('window_days',14)} days — "
                             "a review could turn these into proposals.")
        t = trig(m, "suspend_suggestion")
        if t and len([e for e in evs if e["type"] == "lapse"]) >= t.get("lapse_count", 3):
            lines.append("Several lapses on record. If life has moved on, /suspend is an honorable "
                         "state — this system concluding is allowed to be success.")

    # 4. validator findings
    v = subprocess.run([sys.executable, str(Path(__file__).parent / "validate.py"), "--json"],
                       capture_output=True, text=True, cwd=str(root))
    for f in json.loads(v.stdout or "[]"):
        lines.append(f"validator[{f['level']}] {f['check']}: {f.get('file', '')}")

    banner = "keel boot: " + (" | ".join(lines) if lines else "all clear")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": banner},
                      "systemMessage": banner}))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
