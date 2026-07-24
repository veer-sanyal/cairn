#!/usr/bin/env python3
"""PreToolUse guard for Write|Edit inside a cairn instance. Deny via JSON; all else silent allow."""
import json, sys, os, fnmatch
from pathlib import Path
from cairn_lib import find_root, manifest

def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))
    sys.exit(0)

def main():
    h = json.load(sys.stdin)
    tool = h.get("tool_name", "")
    ti = h.get("tool_input") or {}
    path = ti.get("file_path") or ""
    if tool not in ("Write", "Edit") or not path:
        return
    # a relative file_path is relative to the payload cwd (where the tool acts), not
    # this hook's process cwd — resolving against the wrong base silently allowed
    base = h.get("cwd") or os.getcwd()
    p = Path(path) if Path(path).is_absolute() else Path(base) / path
    root = find_root(base) or find_root(p.parent)
    if not root:
        return
    try:
        rel = str(p.resolve().relative_to(root))
    except ValueError:
        return
    if rel == "state/archive.jsonl":
        deny("archive.jsonl is append-only (cairn invariant). Append via Bash >> "
             "(e.g. printf '%s\\n' '<json>' >> state/archive.jsonl); "
             "/log and cairn_event.py write telemetry, not the archive.")
    if rel.startswith("state/working/") and tool == "Write" and p.exists() \
            and not (root / ".cairn" / "review-in-progress").exists():
        deny("Wholesale overwrite of a working/ file is reserved for /cairn:review "
             "(SKIP/MERGE/INSERT consolidation). Use Edit for targeted fact updates.")
    # ponytail: Edit growth past a cap is not estimated here (old_string/new_string delta
    # is unreliable) — validate.py catches the oversize file at the next boot instead
    if tool == "Write":
        for pat, cap in manifest(root).get("caps", {}).items():
            if (rel == pat or fnmatch.fnmatch(rel, pat)) and \
                    len((ti.get("content") or "").encode()) > cap.get("hard", 1 << 30):
                deny(f"{rel} would exceed its hard size cap ({cap['hard']}B). Context is budgeted (P1): "
                     "move detail to state/working/ or the archive, keep this file an index.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail-soft: never block or crash on our own bug
