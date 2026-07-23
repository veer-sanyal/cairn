# SP4: /cairn:audit — Diagnose Existing Agentic Systems

**Status:** draft for user review
**Date:** 2026-07-23
**Parent:** umbrella spec §7 (SP4 row): "Point the SP3 diagnosis at an existing (non-Cairn) agentic repo: census diff vs actual tool usage, taxonomy audit, elicit-the-north-star interview, emit BUILD/PARK/REJECT fix list."

## Goal

A user with an existing agentic system (any Claude Code setup: CLAUDE.md + skills + hooks + MCP + memory files — not scaffolded by Cairn) runs `/cairn:audit` in that directory and gets: a grounded diagnosis against the level-zero doctrine, a blast-ordered BUILD/PARK/REJECT fix list with every finding citing a principle AND observed evidence (file:line), and an optional migration path to a full Cairn instance.

## Design decisions (locked)

1. **Skill only — zero kernel code.** A non-Cairn repo has no manifest, no telemetry, no hooks contract; every deterministic helper Cairn owns assumes those. The audit is model-driven investigation, reading the repo and citing evidence. The only executables it uses are ones that already exist (`wc -c` for boot-cost measurement via Bash; the vendored research engine if a finding needs domain evidence).

2. **Five stages, reusing SP1–SP3 machinery by reference (never duplicating doctrine):**
   - **Stage 0 — Identify.** If `manifest.json` with `cairn_version` exists → stop, point to `/cairn:review` (auditing a Cairn instance with the blunter tool is a bug). Otherwise map the repo to mechanisms (P23 table): what's resident every session (CLAUDE.md + always-loaded files — measure bytes), what's on-demand, what fires deterministically.
   - **Stage 1 — Elicit the north star (P14/P12).** Interview: what is this system for, in the user's own words; what would "working" look like; does anything measure it today? Artifact-driven — react to what the repo shows, don't run a question battery. Most existing systems have no metric contract; its absence is finding #1, not a blocker.
   - **Stage 2 — Census & data paths (P23, SP3 Stage 1.5 protocol).** Enumerate the environment (session tools, `claude mcp list`), infer the system's data needs from its files/skills, place each need on the data-access ladder, flag rung upgrades ("this skill screenshots a dashboard; a connector for it exists — rung 4 → rung 1").
   - **Stage 3 — Doctrine walk.** Diagnose against the principles with observable evidence only: boot-context cost + distractors (P1/P4 — bytes measured, resident-but-rarely-needed content named), memory discipline (P2/P5 — facts in conversation-dependent places, no archive, stale files with no dates), verification gaps (P16/P21 — "verifier ran" theater, no external correction loop), orchestration misuse (P20 — fan-out where single-threaded is right, or vice versa; multi-writer risks), Goodhart exposure (P18 — chased metrics with no guardrails), boundary gaps (P19 — no ask discipline, rubber-stamp confirmations, irreversible actions ungated), knowledge staleness (P22 — undated cached knowledge, no refresh discipline). Every finding = principle + file:line evidence + severity by blast. No finding without both citations.
   - **Stage 4 — Report & gate.** Findings as BUILD / PARK / REJECT proposals, blast-ordered (P19 ask-order), 2–3 options each with a recommended default (advise-don't-menu, same as the governor). The user is the gate. Offer three dispositions: apply agreed fixes in place; write `AUDIT.md` into the repo (findings + evidence + principle refs, so the trail survives); or **migrate** — hand off to `/cairn:build` with a pre-filled draft (north star from Stage 1, census/data_paths from Stage 2, the repo's existing files mapped to an owner plan) so the interview starts from evidence, not zero.

3. **Fix application follows the boundary contract even though the target repo has none:** reversible file edits = act (with git diff shown); anything destructive or restructuring = ask first; never delete user content — demote/move only. Audit sets up a git commit checkpoint before any edit (refuse to edit a dirty tree without the user's say-so).

4. **No re-litigation across runs:** if `AUDIT.md` exists from a prior run, read it first; a finding the user previously REJECTed only resurfaces with new evidence (same rule as the governor).

## Out of scope
- Auditing non-Claude-Code systems (LangChain apps etc.) — v1 targets the Claude Code ecosystem Cairn understands mechanically (P15 scope).
- Continuous monitoring of audited repos (that's what migration to an instance is for).
- Kernel changes of any kind.

## Testing
- `tests/test_skills_exist.py`: new `"audit"` entry, tokens: `["manifest.json", "/cairn:review", "north star", "ladder", "file:line", "BUILD", "PARK", "REJECT", "AUDIT.md", "blast", "dirty tree"]`.
- No other tests — skill-only change.

## Release
0.6.0. CHANGELOG entry; README command-table row. This completes the umbrella's four sub-projects.
