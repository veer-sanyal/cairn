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
    root = find_root(h.get("cwd") or os.getcwd()) or find_root(Path(path).parent)
    if not root:
        return
    try:
        rel = str(Path(path).resolve().relative_to(root))
    except ValueError:
        return
    if rel == "state/archive.jsonl":
        deny("archive.jsonl is append-only (cairn invariant). Append via the /log command or cairn_event.py.")
    if rel.startswith("state/working/") and tool == "Write" and Path(path).exists() \
            and not (root / ".cairn" / "review-in-progress").exists():
        deny("Wholesale overwrite of a working/ file is reserved for /cairn:review "
             "(SKIP/MERGE/INSERT consolidation). Use Edit for targeted fact updates.")
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
