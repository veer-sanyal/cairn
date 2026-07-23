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

1. **Identify what clears the research bar.** From the domain and the user's own statements,
   list the 2-4 design decisions this instance will encode whose values are empirical
   questions, not preferences. Examples: a study coach → spacing/retrieval-practice
   parameters, session length; a training log → progression cadence, deload/injury
   handling, adherence factors; a project tracker → WIP limits, task-switching costs.
   A decision is researched only when ALL four clear (the guard against researching
   everything):
   - **(a)** the load-bearing claim behind its value is contested or unknown — not settled
     textbook knowledge;
   - **(b)** generalizable external evidence plausibly exists. Personal magic numbers
     (nudge days, session caps, this-user effects) stay **measure-in-telemetry** — grade
     them BET and let reviews tune them; never research them;
   - **(c)** the decision is `blast: med|high` OR one-way — low-blast reversible tweaks
     aren't worth a run;
   - **(d)** the question is narrow enough for one run — one decision per run, never
     bundled. At most one run in flight at a time.
   Anything that fails a clause gets a conservative default + a BET grade. A decision that
   is pure user preference (file layout, tone) needs NO research — do not ceremony-wrap it.
2. **Frame each as a decision, not a topic.** For each: name the design decision it will
   settle, what answering well requires, and what you already know (don't research settled
   textbook knowledge — research what is contested, recent, or quantitative).
3. **Announce the plan in one short list** ("I'll research: X to set Y, Z to set W") and
   proceed by default; the user may trim or skip items. If they skip, every affected
   decision is graded BET in the manifest — never silently ungrounded.
4. **Execute — via the vendored engine.** Follow the /cairn:research skill
   (${CLAUDE_PLUGIN_ROOT}/skills/research/SKILL.md): frame each question as the decision it
   serves, write a GROUNDING block, and launch the plugin's own deep-research workflow
   (Workflow({scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/research/deep-research.js", ...}) —
   pre-scaffold there is no instance copy yet). If the Workflow tool is unavailable, use
   that skill's degraded mode: 2-5 angle subagents, then per-claim adversarial verifiers
   prompted to REFUTE (≥2/3 refutations kill); degraded-mode grades cap at THIN.
5. **Grade and persist.** Persist every run through doctrine_write.py (the /cairn:research
   skill's Step 4): findings land in the instance's `docs/RESEARCH.md` graded VERIFIED
   (survived refutation, high confidence) / THIN (weaker), with a date stamp, perishability
   class, and the refuted claims (do-not-build-on negatives). BET is not a research grade —
   it marks decisions in manifest decisions[] where evidence ran out or research was skipped.
   Every research-backed parameter in the scaffold cites its finding in the manifest
   decisions[] entry.

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
Before asking for confirmation, run ONE fresh-context second opinion — the contract is
the highest-blast decision the instance will ever contain, and a same-context self-review
re-blesses its own reasoning. Spawn a subagent given ONLY the user's goal statement
(Stage 2, verbatim) and the drafted contract, asking: is the north star directly
targetable? is any input a vanity metric? is any guardrail unmeasurable within a review
period? Endorse, or flag with a better alternative. On flag, present the concern with
the table; the user decides. If they proceed over a flag, record it in that decisions[]
entry as `"dissent": "<concern> — user proceeded <date>"`.
Echo the contract back as a table; get explicit confirmation.
Then ONE pairwise governance question: "at review time, may the governor auto-apply
low-stakes reversible tweaks (low-blast, two-way, VERIFIED-backed only — with a 7-day
boot-visible revert window and a self-suspending tripwire), or should it ask about
everything?" → build-config `auto_adopt: true|false`. Default false if they hesitate.

## Stage 4 — If-then compilation (P14)
Convert their goals into if-then rules INTERACTIVELY ("when a week passes with no session,
what should happen?"). **Ask-order: largest blast radius first** — dependencies before
size (never ask a question whose right answer depends on an unanswered upstream one),
contract-level choices before trigger minutiae, and among equals, irreversible (one-way)
choices first. Answering a small question before the big one that governs it wastes the
answer. Map each accepted rule onto the CLOSED trigger-template menu
(spec §2.1): gap_nudge, review_due, staleness_escalation, friction_accumulator,
suspend_suggestion, guardrail regression flag, metric-observation prompts, intent enum.
Parametrize; never invent new
trigger mechanics — menu growth is a kernel-release matter.

## Stage 5 — Scaffold
Assemble the build-config JSON (exact shape documented at the top of skills/build/scaffold.py),
including a decisions[] entry for every design choice with its principle tag, grade
(VERIFIED / PREPRINT / BET), `blast` (low|med|high: what else changes if it flips) and
`one_way` (bool) tags — the governor's ask-order and auto-adopt lane run on these tags.
Write it to a temp file and run:
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
