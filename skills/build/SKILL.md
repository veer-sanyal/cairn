---
name: build
description: Interview the user and scaffold a personalized cairn instance (artifact-driven; user authors the goals)
---

# /cairn:build — the builder

You are building a long-lived personal system for this user. Follow the stages IN ORDER. The
evidence behind each rule is in ${CLAUDE_PLUGIN_ROOT}/docs/PRINCIPLES.md (P-refs inline).

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

## Stage 2.5 — Domain research (unprompted; research serves the design, not curiosity)
The instance's parameters must be grounded in domain evidence the way its kernel is grounded
in agent-systems evidence — WITHOUT the user having to ask for research.

1. **Identify what needs evidence.** From the domain and the user's own statements, list the
   2-4 design decisions this instance will encode whose values are empirical questions, not
   preferences. Examples: a study coach → spacing/retrieval-practice parameters, session
   length; a training log → progression cadence, deload/injury handling, adherence factors;
   a project tracker → WIP limits, task-switching costs. A decision that is pure user
   preference (file layout, tone) needs NO research — do not ceremony-wrap it.
2. **Frame each as a decision, not a topic.** For each: name the design decision it will
   settle, what answering well requires, and what you already know (don't research settled
   textbook knowledge — research what is contested, recent, or quantitative).
3. **Announce the plan in one short list** ("I'll research: X to set Y, Z to set W") and
   proceed by default; the user may trim or skip items. If they skip, every affected
   decision is graded BET in the manifest — never silently ungrounded.
4. **Execute — prefer the strongest available engine.** If a deep-research skill or workflow
   exists in this environment (check the available-skills list for e.g. `deep-research`),
   invoke it with the framed questions. Otherwise run the built-in fallback: for each
   question, spawn 2-3 search subagents on DIFFERENT angles (academic, practitioner,
   contrarian); fetch primary sources over listicles; then for each load-bearing claim spawn
   one adversarial verifier prompted to REFUTE it against the source. Keep only survivors.
5. **Grade and persist.** Write `docs/RESEARCH.md` in the instance: each finding with
   sources, a grade — VERIFIED (multi-source, survived refutation) / THIN (single source) /
   BET (no usable evidence) — a date stamp, and the claims that were refuted (do-not-build-on
   negatives). Every research-backed parameter in the scaffold cites its finding in the
   manifest decisions[] entry.

Hard rule: a refuted or unverified claim never becomes a parameter. Where evidence ran out,
say BET out loud — fake certainty is worse than a labeled guess.

## Stage 3 — Metric contract (P12)
Findings from Stage 2.5 inform the metric DEFAULTS you propose (e.g., evidence-backed cadence
values) — but the user still authors the goals (Stage 2 is untouched by research).
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
    python3 "${CLAUDE_PLUGIN_ROOT}/skills/build/scaffold.py" <config.json> <target-dir>
Then: write `docs/RESEARCH.md` (from Stage 2.5) into the instance, `git init`, commit
"cairn scaffold", run one boot (open a session or invoke session_start manually) to show the
user their banner, and hand over with the three habits that matter: /log real work, trust
the banner, expect the first review after the minimum telemetry window (not sooner —
adoption verdicts wait ~2 months, P13).

## Hard rules
- The interview produces a metric contract BEFORE scaffolding — no contract, no instance.
- Show drafts, don't interrogate. Total interview target: under 15 minutes.
- Never generate freeform hooks or scripts. The scaffolder is the only writer.
