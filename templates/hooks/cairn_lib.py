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

def parse_date(s):
    """ISO date string -> datetime.date, or None on malformed/wrong-typed input.
    The single home for the 'fromisoformat raises TypeError on non-str' rule."""
    try:
        return datetime.date.fromisoformat(s)
    except (ValueError, TypeError):
        return None

def parse_ts(ts):
    """ISO timestamp -> aware datetime (naive assumed UTC), or None on malformed input."""
    try:
        t = datetime.datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None
    return t.replace(tzinfo=datetime.timezone.utc) if t.tzinfo is None else t

def pos_int(x):
    """x if a positive int, else None. Excludes bool (a subclass of int in Python)."""
    return x if isinstance(x, int) and not isinstance(x, bool) and x > 0 else None

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

def append_event(root, etype, **fields):
    ev = {"ts": now_iso(), "type": etype, **fields}
    p = Path(root) / "telemetry" / "events.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev) + "\n")
    return ev

# --- global registry (SP6): a rebuildable cache of instance pointers, never state ---

def registry_path():
    return Path(os.environ.get("CAIRN_HOME", str(Path.home() / ".cairn"))) / "registry.json"

def load_registry():
    """Well-formed registry dict, or a fresh empty one. Corrupt/non-object files are
    coerced — the registry is a cache; instances re-register on their next boot."""
    try:
        data = json.loads(registry_path().read_text())
        if isinstance(data, dict) and isinstance(data.get("instances"), dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return {"version": 1, "instances": {}}

def _write_registry(reg):
    p = registry_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".registry-{os.getpid()}.tmp")  # pid-unique: concurrent boots can't collide
    tmp.write_text(json.dumps(reg, indent=2) + "\n")
    os.replace(tmp, p)

def registry_upsert(root):
    """Upsert this instance into the global registry. Fail-soft: returns bool, never raises.
    Read-modify-write is not locked; a lost race costs one stale field until the next boot."""
    try:
        m = manifest(root)
        inst = m.get("instance") if isinstance(m.get("instance"), dict) else {}
        reg = load_registry()
        reg["instances"][str(Path(root).resolve())] = {
            "name": inst.get("name", ""),
            "purpose": inst.get("purpose", ""),
            "created": inst.get("created", ""),
            "last_session": now_iso(),
            "cairn_version": m.get("cairn_version", ""),
        }
        _write_registry(reg)
        return True
    except Exception:
        return False

def registry_remove(path):
    """Drop one entry (user-confirmed prune). Fail-soft: returns bool, never raises."""
    try:
        reg = load_registry()
        if reg["instances"].pop(path, None) is None:
            return False
        _write_registry(reg)
        return True
    except Exception:
        return False
