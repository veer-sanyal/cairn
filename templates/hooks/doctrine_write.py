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

def main():
    args = sys.argv[1:]
    perish = "semi-durable"
    if "--perishability" in args:
        i = args.index("--perishability"); perish = args[i + 1]; del args[i:i + 2]
    if "--domain" not in args or len(args) < 4:
        sys.exit("usage: doctrine_write.py <result.json> <instance-root> --domain <name>"
                 " [--perishability durable|semi-durable|perishable]")
    i = args.index("--domain"); domain = args[i + 1]; del args[i:i + 2]
    if perish not in REFRESH_DAYS:
        sys.exit(f"unknown perishability class: {perish} (want durable|semi-durable|perishable)")
    result = json.loads(Path(args[0]).read_text())
    root = Path(args[1])
    today = datetime.date.today()
    days = REFRESH_DAYS[perish]
    refresh = (today + datetime.timedelta(days=days)).isoformat() if days else "on contradiction"

    lines = [f"## {domain} — researched {today.isoformat()}",
             f"Perishability: {perish} · Refresh-by: {refresh} · Engine: deep-research (3-vote adversarial)",
             ""]
    findings = result.get("findings") or []
    if result.get("synthesisDegraded") or not findings:
        # never lose the verified layer: fall back to raw confirmed claims
        lines.append("_Synthesis degraded — raw verified claims below._")
        for c in result.get("confirmed") or []:
            g = GRADE.get(c.get("confidence") or "low", "THIN")
            lines.append(f"- **{g}** {c['claim']} (vote {c.get('vote', '?')}) — {c.get('source', '')}")
    else:
        for f in findings:
            g = GRADE.get(f.get("confidence") or "low", "THIN")
            lines.append(f"- **{g}** {f['claim']}")
            if f.get("evidence"):
                lines.append(f"  - evidence: {f['evidence']} (vote {f.get('vote', '?')})")
            lines.append(f"  - sources: {', '.join(f.get('sources') or [])}")
    refuted = result.get("refuted") or []
    if refuted:
        lines += ["", "### Refuted — do not build on"]
        for r in refuted:
            lines.append(f"- {r['claim']} (vote {r.get('vote', '?')}, {r.get('source', '')})")
    if result.get("caveats"):
        lines += ["", "### Caveats", str(result["caveats"])]
    lines.append("")

    out = root / "docs" / "RESEARCH.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    prev = out.read_text() if out.exists() else "# Research findings (instance doctrine)\n\n"
    out.write_text(prev + "\n".join(lines) + "\n")
    print(f"wrote {domain}: {len(findings)} findings, {len(refuted)} refuted -> {out}")

if __name__ == "__main__":
    main()
