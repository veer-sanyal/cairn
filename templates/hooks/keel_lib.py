"""Shared helpers for keel instance hooks. stdlib only; every caller must stay fail-soft."""
import json, os, datetime
from pathlib import Path

def find_root(start):
    """Walk up from start looking for manifest.json with keel_version."""
    p = Path(start).resolve()
    for d in [p, *p.parents]:
        m = d / "manifest.json"
        if m.is_file():
            try:
                if "keel_version" in json.loads(m.read_text()):
                    return d
            except (json.JSONDecodeError, OSError):
                pass
    return None

def manifest(root):
    try:
        return json.loads((Path(root) / "manifest.json").read_text())
    except (json.JSONDecodeError, OSError):
        return {}

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

def append_event(root, etype, **fields):
    ev = {"ts": now_iso(), "type": etype, **fields}
    p = Path(root) / "telemetry" / "events.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev) + "\n")
    return ev
