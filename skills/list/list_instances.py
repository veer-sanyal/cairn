#!/usr/bin/env python3
"""Deterministic reader for /cairn:list. Registry + live per-instance reads → JSON.
Usage: list_instances.py --json | --prune <path> | --register <root>
Plugin-side. Status derivation (SP6 spec §6), precedence order:
  concluded  <- manifest.instance.concluded (authoritative; /conclude sets it)
  suspended  <- last lapse event with deliberate=="true" and cause=="suspended",
                with no `session phase=start` after it (cairn_event stores values as
                strings; a same-session `session phase=end` after the suspend must
                NOT read as activity — that is the tail hazard)
  active     <- otherwise
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "templates" / "hooks"))
from cairn_lib import load_registry, manifest, parse_ts, registry_remove, registry_upsert


def load_events(root):
    p = Path(root) / "telemetry" / "events.jsonl"
    if not p.is_file():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict) and "type" in e and parse_ts(e.get("ts")) is not None:
            out.append(e)
    return out


def status_of(root):
    m = manifest(root)
    inst = m.get("instance") if isinstance(m.get("instance"), dict) else {}
    if inst.get("concluded"):
        return "concluded"
    evs = load_events(root)
    suspends = [e for e in evs if e["type"] == "lapse"
                and e.get("deliberate") == "true" and e.get("cause") == "suspended"]
    if suspends:
        t = parse_ts(suspends[-1]["ts"])
        resumed = any(e for e in evs if e["type"] == "session" and e.get("phase") == "start"
                      and parse_ts(e["ts"]) > t)
        if not resumed:
            return "suspended"
    return "active"


def last_reconciled(root):
    hot = Path(root) / "state" / "HOT.md"
    if not hot.is_file():
        return ""
    mo = re.search(r"^Last reconciled:\s*(\S+)", hot.read_text(), re.MULTILINE)
    return mo.group(1) if mo else ""


def entry_for(path, reg_entry):
    root = Path(path)
    if not (root / "manifest.json").is_file():
        return {"path": path, "name": reg_entry.get("name", ""),
                "purpose": reg_entry.get("purpose", ""), "status": "missing",
                "last_session": reg_entry.get("last_session", ""), "last_reconciled": "",
                "north_star": ""}
    m = manifest(root)
    metrics = m.get("metrics") if isinstance(m.get("metrics"), dict) else {}
    ns = metrics.get("north_star") if isinstance(metrics.get("north_star"), dict) else {}
    return {"path": path, "name": reg_entry.get("name", ""),
            "purpose": reg_entry.get("purpose", ""), "status": status_of(root),
            "last_session": reg_entry.get("last_session", ""),
            "last_reconciled": last_reconciled(root), "north_star": ns.get("name", "")}


def main():
    args = sys.argv[1:]
    if args[:1] == ["--prune"] and len(args) == 2:
        sys.exit(0 if registry_remove(args[1]) else 1)
    if args[:1] == ["--register"] and len(args) == 2:
        sys.exit(0 if registry_upsert(args[1]) else 1)
    reg = load_registry()
    out = [entry_for(p, e) for p, e in sorted(reg["instances"].items())]
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
