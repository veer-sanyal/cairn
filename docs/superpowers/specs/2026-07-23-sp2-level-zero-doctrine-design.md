# SP2: Level-Zero Doctrine (PRINCIPLES.md v2)

**Status:** draft for user review
**Date:** 2026-07-23
**Parent:** `2026-07-23-level-zero-umbrella-design.md` §3 (the twelve-domain map) and §7 (SP2 row). This spec pins structure and process; the *content* requirements per domain are umbrella §3.1–§3.12 and are not restated here.

## Goal

Turn research rounds R5–R9 (`docs/research/research-round{5..9}-*.json`) plus the docs-verified mechanisms reference into PRINCIPLES.md v2: the bundled, evidence-graded, perishability-annotated level-zero doctrine. Retrofit R1–R4-era principles (P1–P15) with the same annotations. Doctrine only — no skill-behavior changes (that is SP3).

## Structure decisions (locked)

1. **Single file, stable numbering.** `docs/PRINCIPLES.md` stays one on-demand file. P1–P15 keep their numbers and content (annotation line added, nothing else changed) — skills cite P-refs and those must not break. New principles are P16–P24, appended in domain order.

2. **Principle ↔ domain ↔ round map:**

| P | Domain (umbrella §) | Source |
|---|---|---|
| P16 | Failure taxonomy (3.2) | R5 |
| P17 | Capability frontier & probing (3.3) | R5 |
| P18 | Objective design & Goodhart resistance (3.4; extends P12) | R7 |
| P19 | Human-agent boundary: delegation, trust, friction, blast radius (3.5 + 3.11) | R8 |
| P20 | Orchestration & model tiering (3.6; extends P3) | R9 |
| P21 | Verification & eval design (3.7) | R6 |
| P22 | Epistemics & knowledge decay (3.8) | R6 |
| P23 | Mechanism selection (3.9) | `research-mechanisms-claude-code-2026-07.md` |
| P24 | Cold start (3.12) | none — explicit [BET] |

Trust & adoption (3.11) folds into P19 and a P13 cross-reference, not its own principle. Perishability classes (3.10) are the annotation schema, not a principle.

3. **Annotation schema.** Directly under every `## N. title` header (all 24), one line:
   `Perishability: durable|semi-durable|perishable · Verified: YYYY-MM · Round: R<n>`
   Mixed-perishability principles annotate the dominant class and note the exception inline (e.g. "taxonomy durable, percentages semi-durable"). Retrofit P1–P15 uses each principle's original round date (R1/R2: 2026-07 pre-existing; judgment per principle for class).

4. **Grade vocabulary unchanged:** [VERIFIED] / [PREPRINT] / [BET] / [REFUTED — do not build on], as the file already defines. New principles carry **curated** refuted entries — only claims someone might plausibly build on (the folk versions: fixed sub-mode percentages, heterogeneous-swarm superiority, unscoped CoT-judging claims, etc.), not all ~60 kills.

5. **Format per new principle** (match existing density, ~15–30 lines each):
   header · annotation line · 2–5 graded findings with one-line source attributions · refuted entries · **Design implications** bullets tying findings to what the builder/governor will do with them (implications may reference future SP3 wiring as "the governor/builder acts on this" without specifying implementation).

6. **Provenance section** at file bottom gains R5–R9 rows (agent counts, confirmed/refuted tallies) and the mechanisms doc reference.

7. **Mechanism selection (P23)** does NOT duplicate the mechanisms reference — it states the selection *doctrine* (decision tree, context-cost logic, census/enumerability consequences) in ~15 lines and cites `docs/research/research-mechanisms-claude-code-2026-07.md` as the load-bearing detail file, same pattern as capabilities/snapshot.md.

## Testing

New `tests/test_principles.py`, extended per task (same pattern as test_skills_exist.py):
- P1–P24 headers all present, in order, numbered exactly once.
- Every principle block contains an annotation line matching `Perishability: (durable|semi-durable|perishable)`.
- Per new principle, 2–4 load-bearing tokens (e.g. P16: "MAST", "self-correct"; P17: "pass^k", "coin-flip"; P18: "Goodhart", "optimization power"; P19: "rubber-stamp", "ask-budget", "act/ask"; P20: "single-writer", "cascade", "15x"; P21: "rubric", "kappa"; P22: "living", "event-triggered"; P23: "hook", "census"; P24: "cold start", "BET").
- Grade-vocabulary line and all four grades still defined in the header block.

## Non-goals

- No behavior wiring (governor sweeps, builder probes) — SP3.
- No doctrine/ directory migration — instance research stays in docs/RESEARCH.md (SP1 decision).
- No re-verification of R1–R4 claims — retrofit annotates, never rewrites.

## Release

Version 0.4.0, CHANGELOG entry "level-zero doctrine". No template/hook changes, so no instance upgrade path needed beyond the version bump.
