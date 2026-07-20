# Keel

**Before:** you ask Claude to help you study; three weeks later the folder is a graveyard of
stale notes and you're re-explaining everything.
**After `/keel:build`:** a 15-minute interview scaffolds a study coach with its own memory
discipline, a metric you chose in your own words, and a monthly review that proposes changes
only your telemetry justifies — and it greets you after a break with "here's where things
stand", not a broken streak.

Keel is a Claude Code plugin that scaffolds long-lived personal agentic systems: a kernel
(file-memory tiers, hook-enforced invariants, local telemetry), a builder (artifact-driven
interview; you author the goals), and a governor (human-gated, telemetry-cited self-improvement).
Every design decision traces to a graded evidence base — see docs/PRINCIPLES.md, produced by
four adversarially-verified research rounds, refuted claims included.

## Install
    /plugin marketplace add veer-sanyal/keel
    /plugin install keel
Then, in an empty directory: `/keel:build`

## What Keel executes on your machine
- Small python3 scripts, all readable in `templates/hooks/` before install and in your
  instance's `.claude/` after. Nothing obfuscated, nothing compiled.
- Only inside instance directories you scaffolded — the plugin registers zero global hooks.
- **Network: never.** Telemetry is local JSONL you can `cat`. No script makes a network call.
- Uninstall the plugin: instances keep working (runtime is instance-local). Delete an
  instance directory: Keel retains nothing about it.
- Platforms: macOS/Linux. Windows is not supported in v1.

## The three ideas (why this isn't another framework)
1. **Metric contract** — no instance exists until you've declared, in your own words, a north
   star (watched, never chased), input levers, and guardrail metrics.
2. **Typed-lapse abandonment model** — lapses are forgot/upkeep/skipped/suspended, recoverable,
   and never guilt-framed; upkeep lapses are treated as Keel bugs. /conclude is a success state.
3. **Human-gated governor** — reviews propose BUILD/PARK/REJECT changes that must cite your
   telemetry; nothing self-applies. (The self-correction literature is clear on why.)

## Docs
docs/PRINCIPLES.md (the evidence), docs/superpowers/specs/ (the design),
docs/research/ (raw verified research). License: MIT.
