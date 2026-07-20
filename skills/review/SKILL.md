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
- No proposal may regress the standing anti-bloat guardrails (boot_context_bytes, ceremony).
- Present as BUILD / PARK / REJECT for the USER to decide — you never apply unasked (the
  self-correction literature is unambiguous: model self-review alone degrades systems).
- Log every proposal + decision: `python3 .claude/hooks/cairn_event.py proposal id=<n> status=<proposed|build|park|reject> cites="<event refs>"`
- For BUILD decisions: apply, then validate empirically (validator clean + the cited friction
  should be re-checked at next review; note the check in the proposal event).
- **Research is a valid proposal.** If a friction cluster traces to a design decision the
  manifest grades BET or THIN, propose a research run (the build skill's Stage 2.5 protocol:
  frame the decision, search primary sources, adversarially verify, update docs/RESEARCH.md
  and re-parametrize) instead of guessing a new value. Also flag docs/RESEARCH.md if its
  date stamp is over a year old in a fast-moving domain — stale evidence is a BET wearing a
  VERIFIED badge.

## Stage 5 — Close
Delete `.cairn/review-in-progress`. Log `python3 .claude/hooks/cairn_event.py proposal id=review status=done`.
Commit everything: "cairn review <date>". Summarize for the user: what moved, what's parked,
when the next review is due.
