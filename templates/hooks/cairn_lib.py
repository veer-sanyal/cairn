"""Shared helpers for cairn instance hooks. stdlib only; every caller must stay fail-soft."""
import json, os, datetime
from pathlib import Path

def find_root(start):
    """Walk up from start looking for manifest.json with cairn_version."""
    p = Path(start).resolve()
    for d in [p, *p.parents]:
        m = d / "manifest.json"
        if m.is_file():
            try:
                data = json.loads(m.read_text())
                # isinstance guard, not `in` on the raw value: a scalar manifest (5, true)
                # would raise TypeError and abort the walk, masking a valid outer root.
                if isinstance(data, dict) and "cairn_version" in data:
                    return d
            except (json.JSONDecodeError, OSError):
                pass
    return None

def manifest(root):
    try:
        data = json.loads((Path(root) / "manifest.json").read_text())
        return data if isinstance(data, dict) else {}   # scalars/lists → {} protects callers
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
