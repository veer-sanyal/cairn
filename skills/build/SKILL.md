---
name: build
description: Interview the user and scaffold a personalized keel instance (artifact-driven; user authors the goals)
---

# /keel:build — the builder

You are building a long-lived personal system for this user. Follow the stages IN ORDER. The
evidence behind each rule is in the plugin's docs/PRINCIPLES.md (P-refs inline).

## Stage 1 — Orient, then show a draft (artifact-based elicitation, P14)
Ask AT MOST three orienting questions (domain; what they're doing today without a system; how
often they realistically show up). Then IMMEDIATELY produce a draft scaffold sketch — proposed
instance name, 2-4 working files with the owner map, intents enum, trigger suggestions with
their parameters — and iterate on the draft with the user. React-to-artifact beats question
batteries. Prefer pairwise choices ("weekly plan file, or per-topic files?") over open ratings.

## Stage 2 — The user authors the goals (P14, PREPRINT-grade but load-bearing)
Ask the user to state, in their own words: what "this system is working" looks like.
You may refine wording for clarity and split compound statements — you MUST NOT write goals
for them or upgrade their phrasing into your own. If they ask you to write it, decline once,
briefly, citing the follow-through evidence (46.6% vs 72.8%), then accept whatever they give.

## Stage 3 — Metric contract (P12)
From their statement derive together:
- north_star: leading, value-representing, NOT directly targetable (if daily work can move it
  directly, it's an input, not the north star)
- inputs: 1-3 levers daily use actually moves
- guardrails: keep the standing ones (boot_context_bytes, upkeep lapse rate) + at most one
  domain guardrail; each must be measurable-within-period, sensitive, timely
Echo the contract back as a table; get explicit confirmation.

## Stage 4 — If-then compilation (P14)
Convert their goals into if-then rules INTERACTIVELY ("when a week passes with no session,
what should happen?"). Map each accepted rule onto the CLOSED trigger-template menu
(spec §2.1): gap_nudge, review_due, staleness_escalation, friction_accumulator,
suspend_suggestion, guardrail regression flag, metric-observation prompts, intent enum.
Parametrize; never invent new
trigger mechanics — menu growth is a kernel-release matter.

## Stage 5 — Scaffold
Assemble the build-config JSON (exact shape documented at the top of skills/build/scaffold.py),
including a decisions[] entry for every design choice with its principle tag and grade
(VERIFIED / PREPRINT / BET). Write it to a temp file and run:
    python3 <plugin>/skills/build/scaffold.py <config.json> <target-dir>
Then: `git init` the instance, commit "keel scaffold", run one boot (open a session or invoke
session_start manually) to show the user their banner, and hand over with the three habits
that matter: /log real work, trust the banner, expect the first review after the minimum
telemetry window (not sooner — adoption verdicts wait ~2 months, P13).

## Hard rules
- The interview produces a metric contract BEFORE scaffolding — no contract, no instance.
- Show drafts, don't interrogate. Total interview target: under 15 minutes.
- Never generate freeform hooks or scripts. The scaffolder is the only writer.
