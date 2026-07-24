#!/usr/bin/env python3
"""Persist a deep-research result JSON as graded findings in docs/RESEARCH.md.
Engine contract (umbrella spec §4): graded findings + refuted list + caveats,
dated, with a perishability class driving the refresh-by date.
Kernel utility, not an event hook (like validate.py): invoked explicitly, so
hard failures are correct here — no exit-0 swallowing.

Grades use the instance vocabulary (build Stage 2.5): VERIFIED / THIN.
Engine confidence high -> VERIFIED; medium/low -> THIN; refuted -> negatives section.

Usage: doctrine_write.py <result.json> <instance-root> --domain <name>
                         [--perishability durable|semi-durable|perishable]
"""
import json, sys, datetime
from pathlib import Path

GRADE = {"high": "VERIFIED", "medium": "THIN", "low": "THIN"}
REFRESH_DAYS = {"durable": None, "semi-durable": 180, "perishable": 60}

# claims come from adversarial web content: collapse whitespace so a newline
# can't mint a fake **VERIFIED** bullet or ## header in RESEARCH.md
def flat(s):
    return " ".join(str(s).split())

def aslist(x):
    # coerce a possibly-wrong-typed field to a list: a bare string sources value must
    # become one source, NOT be iterated character-by-character into RESEARCH.md.
    return x if isinstance(x, list) else ([] if x is None else [x])

def grade(confidence):
    # type-safe: an unhashable confidence (list/dict) must grade THIN, not traceback
    return GRADE.get(confidence, "THIN") if isinstance(confidence, str) else "THIN"

USAGE = ("usage: doctrine_write.py <result.json> <instance-root> --domain <name>"
         " [--perishability durable|semi-durable|perishable]")

def main():
    args = sys.argv[1:]
    perish = "semi-durable"
    if "--perishability" in args:
        i = args.index("--perishability")
        if i + 1 >= len(args):
            sys.exit(USAGE)
        perish = args[i + 1]; del args[i:i + 2]
    if "--domain" not in args or len(args) < 4:
        sys.exit(USAGE)
    i = args.index("--domain")
    if i + 1 >= len(args):
        sys.exit(USAGE)
    domain = flat(args[i + 1]); del args[i:i + 2]
    if perish not in REFRESH_DAYS:
        sys.exit(f"unknown perishability class: {perish} (want durable|semi-durable|perishable)")
    result = json.loads(Path(args[0]).read_text())
    if not isinstance(result, dict):
        sys.exit("result JSON is not an object — nothing to persist")
    root = Path(args[1])
    today = datetime.date.today()
    days = REFRESH_DAYS[perish]
    refresh = (today + datetime.timedelta(days=days)).isoformat() if days else "on contradiction"

    lines = [f"## {domain} — researched {today.isoformat()}",
             f"Perishability: {perish} · Refresh-by: {refresh} · Engine: deep-research (3-vote adversarial)",
             ""]
    # keep only dict entries: a stray string in findings/confirmed/refuted must be
    # skipped, never char-iterated into an AttributeError traceback.
    findings = [f for f in aslist(result.get("findings")) if isinstance(f, dict)]
    confirmed = [c for c in aslist(result.get("confirmed")) if isinstance(c, dict)]
    refuted = [r for r in aslist(result.get("refuted")) if isinstance(r, dict)]
    # refuted-only is legitimate (every claim killed): the do-not-build-on list persists.
    # only a truly-empty run refuses.
    if not findings and not confirmed and not refuted:
        sys.exit("no findings, confirmed, or refuted claims — refusing to write an empty doctrine section")
    # hard failures are correct here (docstring): a claim-less entry must fail LOUD before
    # any write, never land as a silent blank bullet in permanent doctrine.
    for entry in (*findings, *confirmed, *refuted):
        if not flat(entry.get("claim") or ""):
            sys.exit("entry missing 'claim' — refusing to write a blank doctrine line")
    if not findings and not confirmed:
        lines.append("_All candidate claims were refuted — negatives only below._")
    elif result.get("synthesisDegraded") or not findings:
        # never lose the verified layer: fall back to raw confirmed claims
        lines.append("_Synthesis degraded — raw verified claims below._")
        for c in confirmed:
            lines.append(f"- **{grade(c.get('confidence'))}** {flat(c['claim'])} (vote {flat(c.get('vote', '?'))}) — {flat(c.get('source', ''))}")
    else:
        for f in findings:
            lines.append(f"- **{grade(f.get('confidence'))}** {flat(f['claim'])}")
            if f.get("evidence"):
                lines.append(f"  - evidence: {flat(f['evidence'])} (vote {flat(f.get('vote', '?'))})")
            lines.append(f"  - sources: {', '.join(flat(s) for s in aslist(f.get('sources')))}")
    if refuted:
        lines += ["", "### Refuted — do not build on"]
        for r in refuted:
            lines.append(f"- {flat(r.get('claim', ''))} (vote {flat(r.get('vote', '?'))}, {flat(r.get('source', ''))})")
    if result.get("caveats"):
        lines += ["", "### Caveats", flat(result["caveats"])]
    lines.append("")

    out = root / "docs" / "RESEARCH.md"
    if out.parent.exists() and not out.parent.is_dir():
        sys.exit(f"{out.parent} exists but is not a directory — cannot write RESEARCH.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    prev = out.read_text() if out.exists() else "# Research findings (instance doctrine)\n\n"
    out.write_text(prev + "\n".join(lines) + "\n")
    print(f"wrote {domain}: {len(findings)} findings, {len(refuted)} refuted -> {out}")

if __name__ == "__main__":
    main()
