#!/usr/bin/env python3
"""SessionStart: session event + gap look-back + banner from manifest trigger rules."""
import json, sys, os, datetime, subprocess
from pathlib import Path
from cairn_lib import find_root, manifest, append_event, parse_ts

def load_events(root):
    p = Path(root) / "telemetry" / "events.jsonl"
    if not p.is_file():
        return []
    out = []
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Keep only well-formed events — a dict with a type and a parseable ts — so every
        # downstream parse_ts / e["type"] / days_since is safe. One malformed row must not
        # blow up the banner: fail-soft is exit-0, but a lost banner loses all boot guidance.
        if not isinstance(e, dict) or "type" not in e or parse_ts(e.get("ts")) is None:
            continue
        out.append(e)
    return out

def days_since(ts):
    return (datetime.datetime.now(datetime.timezone.utc) - parse_ts(ts)).days

def trig(m, name):
    # type-guarded like validate.py's sweeps: a malformed triggers value (dict, string)
    # must not AttributeError its way into losing the whole banner
    triggers = m.get("triggers")
    triggers = triggers if isinstance(triggers, list) else []
    return next((t for t in triggers if isinstance(t, dict) and t.get("template") == name), None)

def main():
    h = json.load(sys.stdin)
    root = find_root(h.get("cwd") or os.getcwd())
    if not root:
        return
    m = manifest(root)
    if m.get("instance", {}).get("concluded"):
        return  # concluded instances stay silent: readable, never nagging
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
        # exclude the current session: SessionStart re-fires (resume/clear/compact) reuse the id
        sessions = [e for e in evs if e["type"] == "session" and e.get("phase") == "start"
                    and e.get("session_id") != h.get("session_id", "")]
        if sessions:
            last = sessions[-1]
            last_id = last.get("session_id")
            # runtime work events (via cairn_event.py / /log) carry no session_id, so
            # associate by time: any real work event at/after the previous session started.
            last_start = parse_ts(last["ts"])
            worked = any(e for e in evs
                         if e["type"] not in ("session", "lapse")
                         and parse_ts(e["ts"]) >= last_start)
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
        if t and days_since(anchor) >= t.get("days", m.get("cadence", {}).get("review_days", 30)):
            lines.append("A review is due — run /cairn:review when convenient.")
        t = trig(m, "friction_accumulator")
        if t:
            recent = [e for e in evs if e["type"] == "outcome" and e.get("outcome") == "friction"
                      and days_since(e["ts"]) <= t.get("window_days", 14)]
            if len(recent) >= t.get("count", 3):
                lines.append(f"{len(recent)} friction events in {t.get('window_days',14)} days — "
                             "a review could turn these into proposals.")
        t = trig(m, "suspend_suggestion")
        # typed lapses only: "didn't log" (untyped) is not evidence of abandoning
        if t and len([e for e in evs if e["type"] == "lapse"
                      and e.get("cause") != "untyped"]) >= t.get("lapse_count", 3):
            lines.append("Several lapses on record. If life has moved on, /suspend is an honorable "
                         "state — this system concluding is allowed to be success.")

    # auto-adopt revert-window visibility: every in-window adoption is named every boot
    # until the window closes or it's reverted — zero reverts must be distinguishable
    # from zero scrutiny.
    props = [e for e in evs if e["type"] == "proposal"]
    reverted = {e.get("id") for e in props if str(e.get("status", "")).startswith("reverted")}
    today = datetime.date.today().isoformat()
    for e in props:
        if (e.get("status") == "auto_adopted" and e.get("id") not in reverted
                and str(e.get("revert_until", "")) >= today):
            lines.append(f"auto-adopted #{e.get('id')} [blast={e.get('blast', '?')}, "
                         f"door={e.get('door', '?')}] — revert window open to "
                         f"{e.get('revert_until')}; say 'revert #{e.get('id')}' to undo.")

    # guardrail regression flag (spec §2.1): standing anti-bloat check
    for g in m.get("metrics", {}).get("guardrails", []):
        gmax = g.get("max")
        if gmax is None:
            continue
        if g.get("name") == "boot_context_bytes":
            val = resident
        else:
            vals = [e for e in evs if e["type"] == "metric" and e.get("name") == g.get("name")]
            try:
                val = float(vals[-1].get("value")) if vals else None
            except (TypeError, ValueError):
                val = None
        if val is not None and val > gmax:
            lines.append(f"guardrail regression: {g['name']} at {val} (max {gmax}) — review input.")

    # 4. validator findings
    v = subprocess.run([sys.executable, str(Path(__file__).parent / "validate.py"), "--json"],
                       capture_output=True, text=True, cwd=str(root))
    for f in json.loads(v.stdout or "[]"):
        lines.append(f"validator[{f['level']}] {f['check']}: {f.get('file', '')}")

    banner = "cairn boot: " + (" | ".join(lines) if lines else "all clear")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": banner},
                      "systemMessage": banner}))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
