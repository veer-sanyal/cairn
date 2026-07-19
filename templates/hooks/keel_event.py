#!/usr/bin/env python3
"""CLI event writer: keel_event.py TYPE key=val ...  Used by scaffolded commands and hooks."""
import sys, os
from keel_lib import find_root, append_event

def main():
    try:
        if len(sys.argv) < 2:
            return
        root = find_root(os.getcwd())
        if not root:
            return
        fields = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
        append_event(root, sys.argv[1], **fields)
    except Exception:
        pass  # ponytail: fail-soft is the spec'd contract for every runtime script

if __name__ == "__main__":
    main()
