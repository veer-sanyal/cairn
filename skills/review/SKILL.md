---
name: review
description: Run a cairn instance review — validator, memory consolidation (probe→repair→SKIP/MERGE/INSERT), telemetry-cited proposals with the user as gate
---

# /cairn:review — the governor

Run from inside a cairn instance (manifest.json with cairn_version present — verify first).

## Stage 0 — Gate check + sentinel
Read manifest.json cadence. If total sessions < min_sessions AND instance age < min_days:
say so, run ONLY Stage 1 (validation) and Stage 2 (memory lane), skip Stages 3-4 — adoption
judgments before the window are noise (P13). Touch the sentinel file `.cairn/review-in-progress`
NOW (empty file). You MUST delete it at the end — even on failure. A leftover sentinel is
flagged by the validator as stale after 24h.

## Stage 1 — Re-validate invariants (belt-and-suspenders, P9)
Run `python3 .claude/hooks/validate.py --json`. Fix mechanical findings (oversized files:
demote content to working/ or archive; missing stamps: reconcile and stamp). Bash-guard
bypasses and out-of-band edits surface here — this is the real backstop.

## Stage 2 — Memory lane: probe → verify → repair → consolidate (P6, PREPRINT-grade)
1. PROBE: from the last N sessions' events and recent archive entries, synthesize 5-10
   probe questions a well-maintained HOT.md/working set should answer.
2. VERIFY: answer each using ONLY state/HOT.md + state/working/ (spawn a subagent for
   archive lookups — P3). Mark failures.
3. REPAIR: convert each failure into a candidate fact.
4. CONSOLIDATE: for each candidate, decide SKIP (redundant) / MERGE (complements an existing
   entry → Edit that entry) / INSERT (novel → add to the owner file). Wholesale rewrites of a
   working/ file are permitted ONLY in this stage (the sentinel unlocks the guard).
5. Demote: content unreferenced by recent sessions moves working/ → archive (recency-only in
   v1 — a BET, see manifest decisions). Refresh HOT.md and its `Last reconciled:` stamp.

## Stage 3 — Metrics report (P12)
From telemetry/events.jsonl compute and show: north star trend (watched, not chased), each
input metric, each guardrail (flag regressions), lapse events BY TYPE (forgot/upkeep/skipped/
suspended — upkeep lapses are kernel bugs: propose removing the demanding step, not nagging
the user), friction outcomes with notes.

## Stage 4 — System lane: proposals with the user as gate (P10)
For each friction cluster or guardrail regression, draft a proposal. HARD RULES:
- Every proposal cites specific telemetry events (no vibes features).
- **No re-litigation.** Before drafting, scan prior proposal events. A proposal the user
  REJECTed may only return if it cites telemetry events NEWER than the rejection — new
  evidence, not a re-argument. Otherwise don't surface it; the reject event IS the memory.
- **Tag and order by blast.** Every proposal carries `[blast: low|med|high]` (how many
  other decisions / manifest fields / files would have to change if it were adopted then
  flipped) and `[door: one-way|two-way]` (recoverable within one review period?). Present
  dependencies first, then largest blast; among equals, one-way doors first. Never ask a
  question whose right answer depends on an unanswered upstream one.
- No proposal may regress the standing anti-bloat guardrails (boot_context_bytes, ceremony).
- **Advise, don't menu.** Every proposal carries 2-3 mutually exclusive options and a
  recommended default with its grade — pre-chewed to yes/adjust, never a hanging menu.
  The user's attention is the scarce resource.
- Present as BUILD / PARK / REJECT for the USER to decide — you never apply unasked (the
  self-correction literature is unambiguous: model self-review alone degrades systems).
  Exception: the bounded auto-adopt lane below, when the user armed it at build time.
- **Second opinion on weighty user calls (no self-blessing).** When the user makes a call
  that is high-blast, one-way, touches the metric contract, or overrides your
  recommendation: spawn ONE fresh-context subagent given ONLY the framing, the options,
  the manifest metric contract, and the relevant decisions[] entries — never your own
  reasoning or this conversation (a same-context self-review just re-blesses itself).
  It returns endorse, or flag + concern + better alternative. On flag: warn ONCE, before
  recording — state the concern and the alternative in a sentence or two, then the user
  decides. If they proceed, record the decision AND the dissent: add
  `"dissent": "<concern> — user proceeded <date>"` to the new decisions[] entry. Never
  silently accept a call you judge wrong; never re-raise one after it's recorded (it
  returns only under the new-evidence bar above). Low-blast two-way calls are judged
  inline — no subagent ceremony.
- Log every proposal + decision: `python3 .claude/hooks/cairn_event.py proposal id=<n> status=<proposed|build|park|reject> cites="<event refs>" blast=<low|med|high> door=<one-way|two-way>`
- For BUILD decisions: apply, then validate empirically (validator clean + the cited friction
  should be re-checked at next review; note the check in the proposal event).
- **Research is a valid proposal.** If a friction cluster traces to a design decision the
  manifest grades BET or THIN, propose a research run (the build skill's Stage 2.5 protocol:
  frame the decision, search primary sources, adversarially verify, update docs/RESEARCH.md
  and re-parametrize) instead of guessing a new value. Also flag docs/RESEARCH.md if its
  date stamp is over a year old in a fast-moving domain — stale evidence is a BET wearing a
  VERIFIED badge.

### Decision lifecycle — ids are immutable (referential integrity)
`manifest.json` `decisions[]` ids are stable keys, never status labels. Never renumber,
reuse, delete, or rewrite an entry's meaning in place — that breaks every proposal-event
cite and docs/RESEARCH.md reference pointing at it. Changing a decision (a BUILD or
auto-adoption that alters a design choice):
1. Append a NEW entry with the next free id, the new call, its principle/grade/blast/
   one_way tags, and `"supersedes": "<old-id>"`.
2. Annotate the old entry in place: `"status": "superseded", "superseded_by": "<new-id>",
   "superseded_on": "<date>"`. Keep its text — it's the deliberation history.
A live entry needs no status field. Reverting an auto-adoption = the same protocol in
reverse (the revert mints its own superseding entry pointing back).

## Stage 4.5 — Bounded auto-adopt lane (only if manifest `auto_adopt.armed` is true)
A proposal skips the per-item ask and applies immediately ONLY when ALL hold:
- `[blast: low]` AND `[door: two-way]`;
- its backing is graded VERIFIED (a PRINCIPLES.md P-ref or a docs/RESEARCH.md finding that
  survived refutation) — BET / THIN / PREPRINT never auto-adopts;
- it touches none of: the metric contract (north_star / inputs / guardrails), privacy,
  caps, cadence minimums, anything involving money, or text the user authored in their
  own words.
Anything else — including everything when `armed` is false — goes through the normal
BUILD / PARK / REJECT ask. Mechanics (all binding):
- Apply, record the decision change via the lifecycle above, then log:
  `python3 .claude/hooks/cairn_event.py proposal id=<n> status=auto_adopted cites="<event refs>" blast=low door=two-way grade=VERIFIED revert_until=<today+7d>`
- The boot banner names every in-window adoption every session (kernel rule). "revert #n"
  is a plain undo, no ceremony — log it as `status=reverted_merits` (right lane, wrong
  call) or `status=reverted_misgrade` (should never have been eligible).
- **Self-suspending tripwire:** ONE misgrade revert → set `auto_adopt.armed` to `false`
  and record why in `auto_adopt.suspended` IMMEDIATELY. TWO merits reverts within the
  last 10 auto-adoptions → same. Suspended stays suspended until the user explicitly
  re-arms — you never re-arm it yourself.
- **Close-out scan-block:** end the review by listing ALL auto-adoptions from this run in
  one block with their blast/door/grade tags printed — a misgrade must be visible at a
  glance, not buried.

## Stage 5 — Close
Delete `.cairn/review-in-progress`. Log `python3 .claude/hooks/cairn_event.py proposal id=review status=done`.
Commit everything: "cairn review <date>". Summarize for the user: what moved, what's parked,
when the next review is due.
