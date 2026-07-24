# R10: Gaps-Ledger Closeout — Settling the Five Ranked Research Candidates

**Status:** draft for user review
**Date:** 2026-07-24
**Scope:** settles the five ranked research candidates recorded in the 2026-07-23 umbrella spec's honest ledger (§9). Evidence: `docs/research/research-round10-gaps-ledger-closeout.json` (R10 — 175 agents, 7 angles, 45 claims verified / 33 confirmed / 12 killed, 3-vote adversarial, 2026-07-24). This document is the contract the implementation must not contradict; it does not add capability, it grades and wires five defaults that were previously guesses.

**Evidence asymmetry (honest, per the grounding's warning):** two candidates flip to VERIFIED on multiple peer-reviewed primary sources with unanimous adversarial votes; three stay BET on thinner, cross-domain, or single-source evidence — with a materially better-specified design than before. No candidate is left where it started.

---

## Decision 2 — Surrogate-index construction (P18): **BET → VERIFIED (method); apply as discipline, not as the literal estimator**

**Finding (high, unanimous across 12 claims):** a valid leading indicator is *derived*, not guessed. The surrogate index is the predicted value of the lagging north-star given the short-term surrogates; in the linear case each surrogate's treatment effect times its regression coefficient on the primary outcome — objective predictive-power weighting replacing intuition (Athey-Chetty-Imbens-Kang, NBER w26463; Google "Choosing a Proxy Metric", KDD'24). Compose *multiple* short-term signals into ONE index; the composite maps onto Sharpe-ratio portfolio optimization (convex QP) that de-weights correlated proxies. Optimal weighting is sample-size-dependent.

**Failure conditions the doctrine must encode as guardrails:**
- **(a) Prentice's 4th criterion is asymmetric** — it can only *reject* a poor surrogate, never affirmatively *validate* a good one. Failing to reject ≠ validity.
- **(b) Surrogate paradox** — a proxy can harm a subgroup on the true outcome even when population checks and Prentice hold; only the "strong" surrogate (treatment affects the outcome *only* through the surrogate) excludes it assumption-free.
- **(c) Sample-size floor** — a single small dataset cannot credibly validate a surrogate; validation needs large or pooled/meta-analytic data.

**Translation to Cairn (the honest part):** a single personal instance has no RCT + observational two-sample setup, so Cairn cannot run the literal estimator at build time. What flips to VERIFIED is the *construction discipline*, which Cairn can apply:
1. **Compose, don't bet on one.** Prefer a small composite of short-term signals over a single leading indicator.
2. **Weight by predictive power toward the north-star**, not by intuition — and de-weight signals that merely correlate with each other.
3. **Falsify, never confirm.** The builder's causal-validity check (P18 Stage 3) is framed as an attempt to *reject* each candidate proxy — "failing to reject" is the strongest statement available, never "validated."
4. **No small-sample validation.** A proxy is not "confirmed" from a handful of the instance's own events; confirmation waits on accumulated data — which is exactly the shrinkage handover of Decision 3.

**Wiring:** `skills/build/SKILL.md` Stage 3 (north-star derivation + P18 stress test); `docs/PRINCIPLES.md` §18 and the §12 cross-reference.

---

## Decision 3 — Cold-start handover (P24): **BET → VERIFIED (mechanism); REFUTE the fixed "first review" checkpoint**

**Finding (high, all 5 claims 3-0):** the principled handover is not a fixed checkpoint at all. Empirical-Bayes / James-Stein shrinkage shifts control *continuously* as the instance's own-data variance falls below the prior's. The posterior is a precision-weighted blend of inherited doctrine default and own telemetry:

> own-data weight = n / (n₀ + n) = τ² / (τ² + se²)

where n₀ is the doctrine default's implicit sample size (the "authority" it carries) and n is accumulated own-data. The weight rises smoothly toward 1 — this is the literal "data earns authority" formula, no threshold event. James-Stein estimates the shrinkage from the data itself (1 − (p−2)/‖X‖²), needing no preset threshold (Efron 2021; Hoff, Duke).

**Translation to Cairn (python3-stdlib, no stats engine):** discretize the same logic into a rule the review skill can state. Each doctrine default carries an implicit sample size **n₀** (a small integer — its earned authority). A telemetry-cited proposal's own-data weight is `n / (n₀ + n)`, where `n` is the count of relevant own-data events. **Control shifts when `n ≥ n₀`** for that specific default — the instance's telemetry then carries majority weight and may outrank generic doctrine. Below that, doctrine still dominates; the handover is per-default and gradual, not one global "first review" flip.

- **Default n₀ = 5** relevant events (a defensible small-authority prior; the specific value is the residual open knob — the *mechanism* is VERIFIED, the *calibration of n₀* stays BET).
- The invariants (hooks, caps, privacy, the metric contract itself) never hand over — they are not sample-estimated defaults.

**Wiring:** `skills/review/SKILL.md` Stage 4.5 telemetry-handover rule (replace the binary "after first completed review" with the per-default earned-precision rule); `docs/PRINCIPLES.md` §24.

---

## Decision 1 — Goal/preference drift triggers (P14/§8): **KEEP BET, better-specified**

**Finding (medium; 3 supporting claims 3-0, five companion claims killed):** the structural direction — behavioral / variable-window triggers beat a fixed calendar (ADWIN uses a variable-size window over the stream, not a schedule) — is supported. Two things block a flip: the only directly-fetched drift paper (Algorithmic Drift, arXiv:2409.16478) is **simulation-only on synthetic data**; and a confounder — detectors that fire *more often* perform better, but the authors attribute this to the **retraining/refresh** effect, not to better drift *identification*. A naive "fire more behavioral triggers" rule may just be buying refresh.

**Killed companions (do not build on these):** window-size derivability (1-2), a universally-optimal elicitation strategy (0-3), dialogue-progression as the switch signal (0-3), exploration-saturation signal (1-2), plateau-not-drop detection (1-2), RL-recommender manipulation magnitudes (0-3).

**Decision:** keep the current behavioral triggers (repeated typed-lapse pattern OR input metric declined across 2+ review periods) — they are *not* contradicted by any verified evidence — but add the **refresh-confounder caveat** to the doctrine and the review skill so the governor does not conclude "more re-elicitation = better." Do **not** add plateau-detection (its supporting claim was killed). Grade stays BET; the specific signals/windows are labeled unvalidated for live agents, and the settling telemetry (`re_elicit` outcomes, already logged) must separate refresh benefit from genuine drift.

**Wiring:** `skills/review/SKILL.md` goal-drift check; `docs/PRINCIPLES.md` §8 design-implications.

---

## Decision 4 — Ask-budget dose-response (P19): **KEEP default 1, stronger BET**

**Finding (medium, 2-1 on the dose-response framing):** the dose-response *direction* is VERIFIED — clinical alert acceptance drops **~30% for each additional alert per encounter** (negative-binomial IRR ≈ 0.70; Weiner et al. 2017, 1.26M advisories + 326K drug alerts). This is genuine within-session concurrent-burden dose-response and corroborates Kovacs (prompt-every-visit HR 0.78 vs 25%). But it is cross-domain (clinical decision support), measures acceptance decline not abandonment, and the same study found **no** longitudinal desensitization for new alerts. There is no published asks-per-session → abandonment curve for conversational assistants.

**Killed companion (do not rely on it):** the "87.9% / 99.9% near-deterministic habituation lock-in after first dismissal" claim failed 0-3 — **there is no override-lock-in mechanism to lean on.**

**Decision:** keep the conservative **default of 1 ask/session** as a principled floor (per-additional-ask harm rises steeply in every adjacent literature), strengthen its citation with the ~30%/IRR-0.70 gradient, and keep the exact number BET pending in-domain measurement. The first-party dose curve is an open question the instances' own telemetry can eventually supply.

**Wiring:** `skills/build/SKILL.md` boundary contract (ask_budget_per_session); `docs/PRINCIPLES.md` §19.

---

## Decision 5 — Multi-instance / portfolio signals (SP6): **KEEP BET (deferred), design shape recorded**

**Finding (low, single primary source):** beyond names/paths/purpose, a portfolio registry should surface cross-instance signals via a three-part pattern from the noisy-neighbor/fleet-observability literature (US Patent 11,928,518, Kyndryl 2024): (1) **aggregate** multiple pre-existing per-instance telemetry streams into one repository; (2) **correlate** each instance's own patterns into a per-instance "correlated usage pattern"; (3) run cross-instance **impact analysis** (unsupervised anomaly detection, not fixed thresholds) to separate *systemic* from *isolated* failure. This maps directly onto SP6's deferred "meta-review across instances" growth path.

**Decision:** the design *shape* is now specified, but the entire basis is one patent describing an architecture with no measured efficacy — and the open question is explicit: does correlate-then-cross-impact actually beat simple portfolio aggregates for an *agentic* fleet? Unknown without an A/B on real registry data nobody has yet. **Ponytail-correct call: record the shape, do not build it.** SP6's meta-review stays a non-goal; the SP6 spec's future-work section is upgraded from "revisit later" to "here is the validated-shape-but-BET design when a user runs enough instances to want it."

**Wiring:** `docs/superpowers/specs/2026-07-23-sp6-cross-instance-registry-design.md` future-work section only. No code.

---

## Summary of grade changes

| # | Candidate | Principle | Before | After |
|---|-----------|-----------|--------|-------|
| 2 | Surrogate-index construction | P18 | BET | **VERIFIED** (method → construction discipline) |
| 3 | Cold-start handover | P24 | BET | **VERIFIED** (continuous shrinkage; fixed checkpoint refuted) |
| 1 | Drift triggers | P14/§8 | BET | BET, better-specified (+ refresh confounder) |
| 4 | Ask-budget dose-response | P19 | BET | BET, stronger (default 1 held; gradient cited) |
| 5 | Multi-instance patterns | SP6 | BET (deferred) | BET (deferred), design shape recorded |

## Residual open knobs (carried into the ledger, not silently closed)

- **n₀ calibration** (Decision 3): the shrinkage math is settled; the per-metric implicit sample size is a tuning knob, default 5.
- **In-domain ask dose curve** (Decision 4): needs first-party conversational-assistant telemetry.
- **Live-agent drift thresholds** (Decision 1): must be measured with the refresh benefit held separate.
- **Portfolio-pattern efficacy** (Decision 5): needs an A/B on real registry data before SP6 leaves BET.

## Invariants unchanged

No change to: the metric contract shape, watched-not-chased, typed lapses, BUILD/PARK/REJECT with the user as gate, hooks/caps/privacy invariants, boot-context and upkeep guardrails, python3-stdlib-only. This closeout grades and wires defaults; it adds no new capability and no new resident context.
