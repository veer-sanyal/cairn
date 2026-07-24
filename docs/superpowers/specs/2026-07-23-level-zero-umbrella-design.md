# Level-Zero Umbrella: Cairn as a Systems Engineer for Agentic Systems

**Status:** draft for user review
**Date:** 2026-07-23
**Scope:** architecture umbrella pinning the two-tier knowledge design, the level-zero domain map, the vendored research engine, the environment census + data-access ladder, the builder/governor wiring, and the four sub-projects that implement it. Each sub-project gets its own spec → plan → implementation cycle; this document is the contract they must not contradict.

**Evidence base:** research rounds R1–R4 (existing, `docs/research/research-round1..4-*.json`), new rounds R5–R9 (`research-round5-failure-capability.json`, `research-round6-verification-epistemics.json`, `research-round7-objective-design-goodhart.json`, `research-round8-human-agent-boundary.json`, `research-round9-orchestration-tiering.json` — ~860 verification agents total, 3-vote adversarial), and the docs-verified platform reference (`research-mechanisms-claude-code-2026-07.md`). Evidence grades below follow PRINCIPLES.md conventions ([VERIFIED]/[PREPRINT]/[BET]/[REFUTED]).

---

## 1. Purpose and thesis

Cairn's next version is a **systems engineer, not a template dispenser**. It cannot pre-know every system a user might want (a decision-to-code pipeline, a social-anxiety coach, an options-trading advisor). Instead it holds:

1. **Level-zero doctrine** — the knowledge that is true of *every* agentic system: how they fail, how objectives resist corruption, where the human boundary sits, when to fan out, how to verify nondeterministic output, when knowledge expires. Methods and invariants, never domain content.
2. **A research engine** — vendored directing-research + deep-research that *manufactures* the domain-specific doctrine per instance at build time, with evidence grades, and re-manufactures it when it expires.
3. **An environment census** — live discovery of what this user's machine can actually do (MCP servers, surfaces, connectors), because capability is per-machine and perishable.

The trick that makes "literally any system" tractable: **level-zero never contains domain content; domain content is always manufactured, graded, and expiry-tracked.**

### North star for Cairn itself

Cairn's own metric contract (dogfooding §4 of this spec): the north star is *instances still alive-or-honorably-concluded at 90 days* (watched, never chased). Input levers: boot context cost, upkeep burden per week, ask-rate. Guardrails: no instance may regress the standing anti-bloat guardrails; no scaffold without a metric contract.

---

## 2. Two-tier knowledge architecture

```
KERNEL (shipped, versioned with plugin)
  docs/PRINCIPLES.md          — level-zero doctrine, evidence-graded, refresh-by dates
  capabilities/snapshot.md    — platform surface the kernel compiles onto (exists today)
  research engine             — vendored skills + workflow scripts (SP1)

INSTANCE (manufactured at build time, maintained by governor)
  manifest.json               — metric contract + design decisions + census + ladder provenance
  doctrine/DOMAIN.md          — per-instance domain doctrine, same grade vocabulary,
                                each claim carries source + verified-date + perishability class
  telemetry/events.jsonl      — exists today; gains failure-mode tags (§3.2)
```

Every claim in either tier carries three annotations: **evidence grade** (existing vocabulary), **perishability class** (§3.10: durable / semi-durable / perishable), and **verified date**. The governor's expiry sweep (§6) is driven entirely by these three fields — [VERIFIED, R6] models cannot self-detect staleness (~55%, near coinflip), so expiry must be structural metadata, never model judgment.

---

## 3. The level-zero domain map

Twelve domains. Each lists: role, headline evidence, perishability. Full doctrine text is SP2's deliverable (PRINCIPLES.md v2); this section pins what each domain *is* and the strongest finding it must encode.

### 3.1 Elicitation (existing, R4 — carried forward)
Extract the problem behind the stated request before designing. Highest-leverage domain: every downstream error is cheaper than building the wrong system. Semi-durable.

### 3.2 Failure taxonomy (R5)
MAST's 14-mode/3-category taxonomy (system design / inter-agent misalignment / task verification) is canonical [VERIFIED — NeurIPS 2025, kappa 0.88]. Load-bearing findings:
- Failure is the norm, not the tail: 41–86.7% failure rates across 7 SOTA frameworks [VERIFIED].
- Failures are predominantly **design** flaws, not model limits; single design fixes worth +9.4 to +15.6pp [VERIFIED — medium].
- Agents rarely self-correct: 91.49% of resolutions required explicit user correction [VERIFIED, 20,574 real sessions]. Detection must assume the human or an external check is the correction loop.
- "A verifier ran" is a weak signal; verifiers pass functionally-broken output [VERIFIED]. Telemetry must record *what the verifier checked*, not that it ran.
- Errors compound with horizon length and self-condition (a model's own prior errors breed more errors) [VERIFIED].
**Instance wiring:** telemetry events gain an optional `failure_mode` tag drawn from this taxonomy; the governor reads tag frequencies. Durable (taxonomy structure), semi-durable (percentages).

### 3.3 Capability frontier & probing (R5)
The frontier is a *method*, not a list — the fastest-decaying knowledge Cairn touches. Doctrine:
- Reliability is pass^k, never pass@k (pass^8 <25% where single-trial looked fine) [VERIFIED].
- Published horizons (METR) are 50% coin-flip thresholds, not guarantees [VERIFIED].
- Cheap pilots work: a $4.26 / 1,368-episode pilot surfaced real failure modes before a 23K-episode commitment [VERIFIED].
**Builder wiring:** before committing a design to "the model can do X reliably," the builder runs a small pass^k probe (N repeated trials on sampled steps) and records the result in the manifest as a graded, dated claim. Perishable — every frontier claim carries a short refresh window.

### 3.4 Objective design & Goodhart resistance (R7, generalizes existing metric contract)
- Goodhart failure is four distinct mechanisms (regressional / extremal / causal / adversarial), each with a different mitigation [VERIFIED]. Input levers must be *causally* validated; extreme-range behavior can't be assumed from normal-range.
- Severity scales with optimization power — agentic systems are the worst case [VERIFIED verbatim].
- Proxy rewards are theoretically hackable except in degenerate cases (Skalse, NeurIPS 2022) [VERIFIED — medium]. **Consequence: no metric contract is permanently safe; revalidation of every proxy-goal link is a scheduled lifecycle event, not a one-time hardening.**
- LM agents specification-game zero-shot [VERIFIED]. The north star stays non-actionable by design (watched-not-chased survives as doctrine, now with a mechanism).
Caveat carried honestly: leading/lagging-indicator sub-area verified weakly (two canonical-sounding claims refuted 0-3) — grade those sections [BET]. Durable.

### 3.5 Economics of delegation & human-agent boundary (R8)
- Humans are structurally bad at sustained oversight of reliable automation: 33% failure detection under constant reliability vs 82% variable; expertise does not fix it [VERIFIED — canonical human-factors].
- Uniform per-action gating collapses into rubber-stamping (93% approval in Claude Code telemetry) [VERIFIED — first-party].
- The correct structure is Horvitz act/ask/do-nothing with thresholds set by expected utility × blast radius [VERIFIED — CHI 1999 + Anthropic containment framework].
- **Ask-budgets are real:** ask *frequency*, not per-ask cost, drives abandonment (prompt-every-visit vs 25% of visits: HR 0.78) [VERIFIED].
- When friction is spent, make it inhibitive (force interaction with the consequential element): up to −50% unsafe choices, robust to habituation, unlike passive warnings [VERIFIED].
- A token override channel more than doubles adoption of imperfect-but-superior automation [VERIFIED — Dietvorst]. Every instance keeps a user-editable knob even where the data says the default is right.
**Instance wiring:** every scaffolded instance carries an explicit ask-budget and a blast-radius table (§5.3). Durable.

### 3.6 Orchestration & model tiering (R9)
- Default single-threaded; escalate on evidence up the ladder: direct call → single agent with tools → multi-agent [VERIFIED — Azure + practitioner convergence].
- Fan-out fits research-shaped breadth; the 90.2% multi-agent gain came with ~15x tokens, and token budget explains ~80% of variance — fan-out is parallel token spend, not architectural magic [VERIFIED — Anthropic first-party].
- **Single-writer principle:** many readers/advisors, one writer for anything that mutates state [VERIFIED — medium, practitioner doctrine].
- Cascade routing (cheap model first, escalate on low confidence) is the strongest-evidenced cost lever (50–98% cost reduction at ~GPT-4 accuracy) [VERIFIED].
- Quality over diversity: best-of-n from one strong model beats heterogeneous swarms; 2-model consistency-switch matches self-consistency with ~34% fewer samples [PREPRINT].
15 confidently-repeated orchestration claims were refuted — SP2 carries them as explicit [REFUTED] entries. Semi-durable.

### 3.7 Verification & eval design (R6)
- Rubric-first judging: explicit criteria matter more than reference answers; extremes-only score descriptions suffice; mean-of-samples beats greedy; CoT adds little once the rubric is good [VERIFIED].
- Judges are probabilistic instruments: even a 3-model ensemble reaches only kappa 0.432 vs humans, with conservative skew — every judge needs calibration against human labels, verdicts treated as P(correct), never ground truth [VERIFIED].
- Agent evals need trajectory/stage decomposition, not just outcomes: injected faults propagate to wrong answers ~62% of the time; outcome metrics can't localize [VERIFIED].
- For binary verdicts report kappa + one correlation; all others collapse to the same number [VERIFIED — mathematical].
Durable (methods), semi-durable (magnitudes).

### 3.8 Epistemics & knowledge decay (R6)
The living-systematic-review discipline, imported:
- Staleness is **event-triggered, not clock-driven** ("does new evidence change conclusions?"), with cheap continuous surveillance decoupled from expensive full re-verification.
- Entry/exit criteria for "living" mode: decision priority × low certainty × likely new evidence.
- Hard ceilings: ~6-month max incorporation window; annual re-review even if nothing changed.
- Models cannot self-detect staleness (~55%) [VERIFIED] — triggers are structural (dependency graphs, dated claims, census diffs), never model self-assessment.
This domain is what makes per-system research *sustainable*: only perishable claims get re-researched. Durable.

### 3.9 Mechanism selection (docs-verified reference)
When to use hook / skill / subagent / workflow / MCP / CLAUDE.md / plugin — decision tree and cost profiles in `research-mechanisms-claude-code-2026-07.md`. Bundled like capabilities/snapshot.md with a refresh-by date tied to Claude Code releases. Perishable (platform-versioned).

### 3.10 Perishability classes (cross-cutting)
- **Durable** (control theory, human factors, Goodhart mechanisms): refresh on contradiction only.
- **Semi-durable** (taxonomies' percentages, orchestration economics): refresh-by ~2 releases.
- **Perishable** (capability frontier, platform surface, census): dated, short windows, probe-not-recall.

### 3.11 Trust & adoption (R8 + existing R3)
Subsumes friction economics (§3.5 findings), the override-channel result, and R3's lapse typology. Already partially implemented (typed lapses, no streaks); SP2 merges the general evidence in. Durable.

### 3.12 Cold start (cross-cutting) [BET]
A fresh instance has zero telemetry. Doctrine: defensible defaults come from level-zero (ask-budgets, blast-radius table, single-writer) + the build-time research round; control shifts to instance data on a declared schedule (first governor review). Graded [BET] — no direct research round; revisit if it earns one.

---

## 4. The research engine (SP1)

**Vendoring (user decision, locked):** Cairn vendors its own copies of directing-research + deep-research; no dependency on the user's global setup.

**Platform constraint [VERIFIED — docs]:** plugins cannot ship saved workflows. Therefore:
- `skills/research/` — vendored directing-research discipline (framing, GROUNDING blocks, scope-to-decision) as a Cairn skill, plus the deep-research workflow `.js` carried as a **skill supporting file**, launched via `Workflow({scriptPath: <plugin path>})`.
- The scaffolder additionally copies the workflow script into each instance's `.claude/workflows/` so instances get `/deep-research` natively.
- Claim-scaled sizing is preserved (angles 2–8 from breadth, verification budget from claim volume, per-angle floors) — this is the property the user called out as essential.
- Model tiering inside the engine follows §3.6: cheap tiers for search/fetch/verify fan-out, session model for scope/synthesis (already the vendored script's design).

**Engine contract:** input is always a *framed decision* + GROUNDING block (directing-research is the mandatory front door — the builder and governor never call deep-research raw). Output is always graded findings + refuted list + caveats, written to the instance's `doctrine/` with dates and perishability classes.

---

## 5. Environment census & data-access ladder (SP3, used by SP4)

### 5.1 Census
At build time (and every governor review), enumerate: MCP servers (`claude mcp list` / session tool list), skills (slash-command list), surfaces (Chrome, computer-use — detected via server presence; no feature-detection API exists [VERIFIED — docs]). Recorded in `manifest.json` with a date. Tool *schemas* are not queryable — capability is inferred from server identity.

### 5.2 Data-access ladder
For every data need the design surfaces, try in order and **record the rung + reason in the manifest**:
1. Connected MCP/API.
2. Connector that exists but isn't installed → propose installation (web-lookup discovery; there is no registry-search API [VERIFIED — docs], so rung 2 is manual-assisted, never automatic).
3. Browser automation on the authenticated web app.
4. Screenshot + vision where the DOM resists.
5. Manual user entry.
Governor diff: census change + recorded rung → upgrade proposal ("rung 1 became available for chart data; currently on rung 4").

### 5.3 Blast-radius table (every instance)
Actions classed by reversibility; autonomy inversely proportional to irreversibility (Horvitz act/ask/do-nothing × Anthropic likelihood-×-damage). Reversible-in-instance: act. Reversible-outside: act + log. Hard-to-reverse / outward-facing: ask (inhibitive friction, not a passive confirm). Irreversible + external: never autonomous. Charged against the instance ask-budget (§3.5).

---

## 6. Wiring into builder and governor (SP3)

**Builder (A→B):** interview (existing, R4) → diagnosis against the failure taxonomy ("this design invites FM-3.2-class failure; adding a checked verifier") → capability probes for any load-bearing "the model can do X" assumption (§3.3) → census + ladder for every data need → mechanism/orchestration selection per §3.6/§3.9 → domain research round via the engine (§4) → scaffold with metric contract + ask-budget + blast-radius table + instance doctrine.

**Governor (C):** existing review loop gains four sweeps, all evidence-gated (BUILD/PARK/REJECT unchanged, user remains the gate):
1. **Expiry sweep** — dated claims past their perishability window → re-research proposals (event-triggered surveillance first, full re-run only when surveillance says conclusions may change).
2. **Census diff** — new/removed capabilities → ladder-upgrade proposals.
3. **Failure-mode audit** — telemetry `failure_mode` tag frequencies vs taxonomy → de-automation or design-fix proposals ("this task class failed 3×; propose moving it below the autonomy line").
4. **Proxy revalidation** — scheduled Goodhart check of every input-lever→north-star link (§3.4: no contract is permanently safe).

---

## 7. Sub-project decomposition (build order locked)

| # | Sub-project | Delivers | Depends on |
|---|---|---|---|
| SP1 | Research engine vendoring | `skills/research/` (directing-research discipline + deep-research script as supporting file), scaffolder copy-into-instance, engine contract | — |
| SP2 | Level-zero doctrine | PRINCIPLES.md v2 from R5–R9 (including [REFUTED] entries), perishability/verified-date annotations on all claims incl. retrofitting R1–R4, mechanism-selection doc integration | SP1 (engine formats), R5–R9 (done) |
| SP3 | Builder + governor wiring | Census, ladder, capability probes, failure-mode telemetry tags, the four governor sweeps, ask-budget + blast-radius scaffolding | SP1, SP2 |
| SP4 | `/cairn:audit` | Point the SP3 diagnosis at an existing (non-Cairn) agentic repo: census diff vs actual tool usage, taxonomy audit, elicit-the-north-star interview, emit BUILD/PARK/REJECT fix list | SP3 |

Each sub-project: own spec → plan → implementation → review, per the existing superpowers flow.

---

## 8. Invariants carried forward (unchanged, binding on all sub-projects)

- Metric contract or no instance; north star watched-never-chased (now mechanism-backed by §3.4).
- Standing anti-bloat guardrails: boot context cost and upkeep burden may not regress — every SP3 addition (census, doctrine files) loads on demand, never at boot; HOT.md stays lean.
- Hooks: exit-0 discipline, deny-as-JSON, no new always-resident context.
- Lapses typed, never shamed; `/conclude` is a success state.
- python3 stdlib only; instance works with plain Claude Code if the plugin is uninstalled.
- Every proposal to change an instance is evidence-gated and user-approved (BUILD/PARK/REJECT).

## 9. Known gaps & open questions (honest ledger)

- Leading/lagging-indicator doctrine is weak ([BET]) — two canonical claims refuted; watch for better evidence.
- No MCP registry-search API — ladder rung 2 stays manual-assisted until one ships.
- Cold start (§3.12) has no dedicated research round.
- Cheap-swarm enthusiasm is *capped* by R9: heterogeneous swarms lost to best-of-n from a strong model; the tiering selector must encode this, not the folk version.
- Judge calibration against human labels requires *the user* to label a small set for any instance that builds its own judge — this is an ask-budget expense SP3 must price in.
- Workflow availability requires Pro+/API and can be disabled (`disableWorkflows`) — SP1 needs a degraded-mode path (subagent-based research fallback).
- P11 session-stamping is approximated: runtime work events carry no session_id — association is by timestamp window (session_start.py). A recorded kernel deviation; revisit if telemetry mis-association ever surfaces in review.
- Probe-tagging idea (P5): when a Stage-2 memory probe fails and the missing fact turns out to have been demoted working→archive, tag the failure `demotion_miss` — those events are the direct evidence stream for P5's PREPRINT-grade decay-formula bet (recency-only demotion in v1). Not yet implemented; costs one tag, buys the bet its settling telemetry.
- Open-bets cross-reference: the 2026-07-19 design spec's "'Unfilled niche' beyond Claude Code ecosystem" bet row is unchanged by the 2026-07-23 README broadening — that rewrite is domain-generality *framing* (Cairn builds systems for any domain), not a competitive-uniqueness claim; the niche question still awaits verification before public positioning.

### Ranked research candidates (2026-07-24 audit; locked decision 8 — recorded here, not executed in the 0.8.1 pass)

| # | Candidate | Principle | Decision it would settle |
|---|---|---|---|
| 1 | Drift / re-elicitation triggers | P14 | Which behavioral signals (typed-lapse patterns, input-metric decline windows) should fire the governor's goal-drift check — current 2-review-period heuristic is a BET |
| 2 | Surrogate-index construction (Athey et al. econometrics; clinical surrogate-endpoint criteria) | P18 | How the builder derives a valid leading indicator from a lagging outcome — the construction method behind every north-star proposal |
| 3 | Cold-start handover | P24 | Whether first-completed-review is the right doctrine→telemetry handover point, and what evidence volume "earns authority" |
| 4 | Ask-budget dose-response | P19 | The default ask_budget_per_session value (currently 1) — Kovacs gives frequency-harms direction, not a dose curve |
| 5 | Multi-instance patterns | SP6 | What cross-instance signals (shared lapse patterns, portfolio-level metrics) the registry should surface beyond names/paths/purpose |
