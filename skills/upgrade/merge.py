#!/usr/bin/env python3
"""Managed-file merge for /keel:upgrade. Usage: merge.py <new> <installed> [--original <shipped-at-install>]
Rule (spec: no silent data loss): unmanaged or user-modified files are never overwritten —
the new version lands as <installed>.keel-new instead."""
import sys, re, shutil
from pathlib import Path

HEADER = re.compile(r"managed-by-keel:\s*([\d.]+)")

def main():
    args = sys.argv[1:]
    orig = None
    if "--original" in args:
        i = args.index("--original")
        orig = Path(args[i + 1]); del args[i:i + 2]
    new, installed = Path(args[0]), Path(args[1])
    inst_text = installed.read_text() if installed.exists() else None
    if inst_text is None:
        shutil.copy(new, installed); return                       # fresh file
    if not HEADER.search(inst_text):
        return                                                    # user's own file: never touch
    unmodified = orig is not None and inst_text == orig.read_text()
    if unmodified:
        shutil.copy(new, installed)
    else:
        shutil.copy(new, installed.with_name(installed.name + ".keel-new"))

if __name__ == "__main__":
    main()
