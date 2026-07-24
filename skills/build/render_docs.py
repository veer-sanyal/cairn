#!/usr/bin/env python3
"""Render an instance's human-facing docs (README.md + docs/MANUAL.md) from its manifest.
Usage: render_docs.py <manifest.json> <output-dir>

Single source of truth for both callers: the scaffolder (fresh instance) and /cairn:upgrade
(existing instance — renders to a temp dir, then merges so user edits are never clobbered).
Everything the docs show — the metric contract, intents, ask-budget, cadence — is read from
manifest.json, so `/help` reading the live manifest and these generated docs never disagree.
"""
import json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
T = REPO / "templates" / "instance"
PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def render(tmpl, subs):
    # Validate the TEMPLATE (trusted), never the substituted output: user content that
    # legitimately says "{{today}}" must survive. Same contract as scaffold.py's render().
    unknown = {name for name in PLACEHOLDER.findall(tmpl) if name not in subs}
    if unknown:
        sys.exit(f"template has unrendered placeholder(s): {', '.join(sorted(unknown))}")
    if "{{" in PLACEHOLDER.sub("", tmpl):
        sys.exit("template contains a malformed '{{' placeholder (non-word name?)")
    return PLACEHOLDER.sub(lambda mo: str(subs[mo.group(1)]), tmpl)


def _input_line(i):
    name = i.get("name", "(unnamed)")
    return f"- **{name}**"


def _guardrail_line(g):
    name = g.get("name", "(unnamed)")
    mx = g.get("max")
    return f"- **{name}** — hard limit: {mx}" if mx is not None else f"- **{name}**"


def build_subs(manifest):
    inst = manifest.get("instance", {}) if isinstance(manifest.get("instance"), dict) else {}
    metrics = manifest.get("metrics", {}) if isinstance(manifest.get("metrics"), dict) else {}
    ns = metrics.get("north_star", {}) if isinstance(metrics.get("north_star"), dict) else {}
    inputs = metrics.get("inputs", []) if isinstance(metrics.get("inputs"), list) else []
    guardrails = metrics.get("guardrails", []) if isinstance(metrics.get("guardrails"), list) else []
    cadence = manifest.get("cadence", {}) if isinstance(manifest.get("cadence"), dict) else {}
    boundary = manifest.get("boundary", {}) if isinstance(manifest.get("boundary"), dict) else {}
    intents = manifest.get("intents", []) if isinstance(manifest.get("intents"), list) else []
    return {
        "cairn_version": manifest.get("cairn_version", ""),
        "instance_name": inst.get("name", manifest.get("instance_name", "this system")),
        "one_line_purpose": inst.get("purpose", ""),
        "north_star_name": ns.get("name", "(not set)"),
        "north_star_statement": ns.get("statement", "(not set)"),
        "inputs_block": "\n".join(_input_line(i) for i in inputs)
            or "- _(none defined yet — a review can add levers once telemetry shows what moves the north star)_",
        "guardrails_block": "\n".join(_guardrail_line(g) for g in guardrails)
            or "- _(none beyond the standing kernel guardrails: boot-context size and upkeep burden)_",
        "intents": ", ".join(str(x) for x in intents) or "work",
        "review_days": cadence.get("review_days", 30),
        "ask_budget": boundary.get("ask_budget_per_session", 1),
    }


def _write_generated(target, text):
    """Write a generated doc, but never clobber a file the user has made their own.
    These docs are regenerated on every manifest change (scaffold, review, upgrade), so
    overwrite-in-place is the norm — EXCEPT if the existing file dropped the managed-by-cairn
    header, which means the user replaced it deliberately. Then leave it and report."""
    if target.exists() and "managed-by-cairn" not in target.read_text():
        print(f"kept (user-owned, no managed header): {target}", file=sys.stderr)
        return False
    target.write_text(text)
    return True


def write_docs(manifest, out_dir):
    """Render README.md and docs/MANUAL.md for `manifest` into `out_dir`. Idempotent and
    safe to re-run: regenerates in place from the manifest, skips user-owned overrides."""
    out = Path(out_dir)
    subs = build_subs(manifest)
    (out / "docs").mkdir(parents=True, exist_ok=True)
    _write_generated(out / "README.md", render((T / "README.md.tmpl").read_text(), subs))
    _write_generated(out / "docs" / "MANUAL.md", render((T / "docs" / "MANUAL.md.tmpl").read_text(), subs))


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: render_docs.py <manifest.json> <output-dir>")
    manifest = json.loads(Path(sys.argv[1]).read_text())
    write_docs(manifest, sys.argv[2])
    print(f"rendered README.md + docs/MANUAL.md into {sys.argv[2]}")


if __name__ == "__main__":
    main()
