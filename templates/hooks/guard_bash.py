#!/usr/bin/env python3
"""Heuristic Bash guard for cairn-protected paths. Known-incomplete by design (spec §1.3):
review re-validation is the real backstop. Patterns cover the common destructive forms."""
import json, re, sys, os
from cairn_lib import find_root

PROTECTED = r"(state/(?:working|archive\.jsonl)|telemetry/events\.jsonl)"
PATTERNS = [
    re.compile(r"\brm\b[^;&|\n]*" + PROTECTED),             # rm on protected paths (single command)
    re.compile(r"(?<!>)>(?!>)\s*\S*" + PROTECTED),          # single-> truncation (>> is allowed)
    re.compile(r"\b(truncate|shred)\b[^;&|\n]*" + PROTECTED),
    re.compile(r"\bmv\b[^;&|\n]*state/archive\.jsonl"),
    # overwrite-verb parity: a protected path as the WRITE target of these is the same
    # truncation `>` already denies (reads — cp FROM, sed without -i — stay allowed)
    re.compile(r"\b(cp|install)\b[^;&|\n]*\s\S*" + PROTECTED + r"\s*(?:$|[;&|\n])"),  # dest = last arg
    re.compile(r"\btee\b[^;&|\n]*" + PROTECTED),
    re.compile(r"\bdd\b[^;&|\n]*\bof=\S*" + PROTECTED),
    re.compile(r"\bsort\b[^;&|\n]*-o\s*\S*" + PROTECTED),
    re.compile(r"\bsed\b[^;&|\n]*\s-i[^;&|\n]*" + PROTECTED),
]

def main():
    h = json.load(sys.stdin)
    if h.get("tool_name") != "Bash":
        return
    if not find_root(h.get("cwd") or os.getcwd()):
        return
    cmd = (h.get("tool_input") or {}).get("command") or ""
    for p in PATTERNS:
        if p.search(cmd):
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    "This command targets a cairn-protected file (archive/working are guarded; "
                    "archive is append-only — use >> or cairn_event.py; working/ changes go "
                    "through Edit or /cairn:review)."}}))
            return

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
