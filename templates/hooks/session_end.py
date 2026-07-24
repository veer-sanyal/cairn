#!/usr/bin/env python3
"""SessionEnd: close the session record. SessionEnd cannot feed context; file-write only."""
import json, sys, os, datetime
from pathlib import Path
from cairn_lib import find_root, append_event

def main():
    h = json.load(sys.stdin)
    root = find_root(h.get("cwd") or os.getcwd())
    if not root:
        return
    sid = h.get("session_id", "")
    dur = 0
    p = Path(root) / "telemetry" / "events.jsonl"
    if p.is_file():
        for line in p.read_text().splitlines():
            try:
                e = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(e, dict) and e.get("type") == "session" and e.get("phase") == "start" and e.get("session_id") == sid:
                # normalize a naive ts to UTC (else tz-aware minus tz-naive → TypeError,
                # which would drop the end record entirely); a bad ts just leaves dur=0.
                try:
                    start = datetime.datetime.fromisoformat(e["ts"])
                    if start.tzinfo is None:
                        start = start.replace(tzinfo=datetime.timezone.utc)
                    dur = int((datetime.datetime.now(datetime.timezone.utc) - start).total_seconds())
                except (KeyError, ValueError, TypeError):
                    pass
    append_event(root, "session", phase="end", session_id=sid,
                 duration_s=max(dur, 0), reason=h.get("reason", ""))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
