#!/usr/bin/env python3
"""CLI event writer: cairn_event.py TYPE key=val ...  Used by scaffolded commands and hooks."""
import sys, os
from pathlib import Path
from cairn_lib import find_root, append_event

def main():
    try:
        if len(sys.argv) < 2:
            return
        # cwd first (normal in-instance invocation); fall back to the script's own
        # location — it lives in <instance>/.claude/hooks/, so an absolute-path
        # invocation from an outside cwd still finds its instance (B2)
        root = find_root(os.getcwd()) or find_root(Path(__file__).resolve())
        if not root:
            return
        fields = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
        append_event(root, sys.argv[1], **fields)
    except Exception:
        pass  # ponytail: fail-soft is the spec'd contract for every runtime script

if __name__ == "__main__":
    main()
