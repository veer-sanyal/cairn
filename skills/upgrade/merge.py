#!/usr/bin/env python3
"""Managed-file merge for /cairn:upgrade. Usage: merge.py <new> <installed> [--original <shipped-at-install>]
Rule (spec: no silent data loss): unmanaged or user-modified files are never overwritten —
the new version lands as <installed>.cairn-new instead. Prints the action taken."""
import sys, re, shutil
from pathlib import Path

HEADER = re.compile(r"managed-by-cairn:\s*([\d.]+)")

def main():
    args = sys.argv[1:]
    orig = None
    if "--original" in args:
        i = args.index("--original")
        orig = Path(args[i + 1]); del args[i:i + 2]
    new, installed = Path(args[0]), Path(args[1])
    inst_text = installed.read_text() if installed.exists() else None
    if inst_text is None:
        shutil.copy(new, installed)
        print(f"copied (new file): {installed}"); return
    if inst_text == new.read_text():
        print(f"identical: {installed}"); return
    if not HEADER.search(inst_text):
        print(f"untouched (unmanaged): {installed}"); return          # user's own file: never touch
    if orig is not None and inst_text == orig.read_text():
        shutil.copy(new, installed)
        print(f"replaced: {installed}")
    else:
        # shutil.copy overwrites any stale .cairn-new from a skipped upgrade — latest wins
        shutil.copy(new, installed.with_name(installed.name + ".cairn-new"))
        print(f"kept, new version at {installed}.cairn-new")

if __name__ == "__main__":
    main()
