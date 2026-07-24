#!/usr/bin/env python3
"""SessionEnd: close the session record. SessionEnd cannot feed context; file-write only."""
import json, sys, os, datetime
from pathlib import Path
from cairn_lib import find_root, append_event, parse_ts, read_text_safe

def main():
    h = json.load(sys.stdin)
    root = find_root(h.get("cwd") or os.getcwd())
    if not root:
        return
    sid = h.get("session_id", "")
    dur = 0
    p = Path(root) / "telemetry" / "events.jsonl"
    if p.is_file():
        for line in read_text_safe(p).splitlines():
            try:
                e = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(e, dict) and e.get("type") == "session" and e.get("phase") == "start" and e.get("session_id") == sid:
                # shared parse_ts normalizes a naive ts to UTC and returns None on a bad
                # one — a malformed start ts just leaves dur=0, never drops the end record.
                start = parse_ts(e.get("ts"))
                if start is not None:
                    dur = int((datetime.datetime.now(datetime.timezone.utc) - start).total_seconds())
    append_event(root, "session", phase="end", session_id=sid,
                 duration_s=max(dur, 0), reason=h.get("reason", ""))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
