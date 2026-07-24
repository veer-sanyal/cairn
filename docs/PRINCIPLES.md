# Principles for Resilient Personal Agentic Systems

Research-derived design principles. Every principle carries an evidence grade:

- **[VERIFIED]** — survived 3-vote adversarial verification against primary sources; multi-source or first-party primary documentation.
- **[PREPRINT]** — survived verification but rests on 2025–2026 preprints / benchmark-only results; treat as an informed bet.
- **[BET]** — no surviving evidence either way; a reasoned design decision, labeled as such.
- **[REFUTED]** — claims that FAILED verification and must not be cited or built on.

Every principle carries an annotation line: `Perishability: durable|semi-durable|perishable · Verified: YYYY-MM · Round: R<n>` — durable refreshes on contradiction only, semi-durable within ~2 releases, perishable is probe-not-recall (short windows). The governor's expiry sweep (SP3) reads the equivalent `Refresh-by`/`researched` dates in each instance's docs/RESEARCH.md; the annotations in THIS file are enforced by the repo's own test suite (age checks in tests/test_principles.py: any principle >12 months old fails, perishable >6 months fails).

Sources are listed per principle. Rounds: R1 = context/memory, R2 = enforcement/self-improvement, R3 = telemetry/abandonment, R4 = elicitation/prior art, R5 = failure/capability, R6 = verification/epistemics, R7 = objective design/Goodhart, R8 = human-agent boundary, R9 = orchestration/tiering. Full per-round provenance is in "## Research provenance" at the end of this file.

---

## 1. Context is a budgeted, degrading resource
Perishability: semi-durable · Verified: 2026-07 · Round: R1

**[VERIFIED]** Recall accuracy degrades non-uniformly and increasingly unreliably as input tokens grow, even at constant task complexity, across all 18 models tested; distractor content compounds degradation (1 distractor hurts, 4 hurt more).
Sources: Chroma "Context Rot" (18-model primary study); Anthropic engineering blog (cites it as foundational). Caveat: Chroma sells retrieval infra (motive, not methodology, questioned).

**Design implications:**
- Minimize resident tokens by default. A thin routing entry file, not a fat one.
- Anything not needed this turn is a distractor — it actively hurts, it isn't neutral.

## 2. Fine-grained facts live in files, never in summarized history
Perishability: semi-durable · Verified: 2026-07 · Round: R1

**[VERIFIED]** Compaction halves peak context (169K vs 335K tokens in Anthropic's cookbook run) but is measurably lossy in a specific pattern: high-level facts survived 3/3 recall probes, obscure specifics 0/3. Tool-result clearing cut message-list size 67% at zero inference cost. Without management, a research agent hit a 200K hard limit mid-task at turn 3.
Sources: Anthropic cookbook (context-engineering tools), Anthropic engineering blog. Caveat: single-vendor illustrative demo runs; treat magnitudes as illustrative, direction as solid.

**[VERIFIED — medium]** File memory is the only mitigation that works across sessions; compaction/clearing operate on the current context only. Anthropic two-session test: with a ~3K-token findings file, session 2 built incrementally; without it, full re-research.

**Design implications:**
- Write-through to files during work; never rely on conversation history or compaction summaries for specifics.
- Session boundaries are only survivable via files.

## 3. Sub-agent fan-out isolates context; returns are condensed
Perishability: semi-durable · Verified: 2026-07 · Round: R1

**[VERIFIED]** Sub-agents explore extensively (tens of thousands of tokens) in their own windows and return condensed summaries (often 1–2K tokens). Detailed search context stays isolated from the orchestrator.
Source: Anthropic engineering blog ("often", not a hard constant).

**Design implication:** exploration/noisy reads are scaffolded as spawned agents with a summary-size norm on returns — never in the main session.

## 4. Index-first layout; progressive disclosure
Perishability: semi-durable · Verified: 2026-07 · Round: R1

**[VERIFIED]** Agents should hold lightweight identifiers (paths, stored queries, links) and load content just-in-time, exploiting cheap metadata: file size ≈ complexity, naming ≈ purpose, timestamps ≈ relevance.
Source: Anthropic engineering blog. Tradeoff (noted by Cognition/Inkeep, undisputed): runtime exploration is slower.

**[REFUTED — do not build on]** "Filesystem as the SOLE authoritative record of task state" (InfiAgent claim, 1-2). Files are the durable tier, not a claim that nothing may live in context.

**Design implications:**
- Small index files pointing at content files; the index is what boots, content loads on demand.
- Naming/size/timestamp conventions are part of the API surface for the agent.

## 5. Tiered hot/cold memory with scored promotion/demotion — not deletion
Perishability: durable · Verified: 2026-07 · Round: R1

**[VERIFIED]** The convergent architecture across MemGPT → MemoryOS → HMO: a small active tier (recent sessions + top-K pivotal memories), a working/buffer tier (high-scoring overflow), and a full append-only archive, with promotion/relegation driven by relevance to an evolving user model.
Sources: MemGPT (arXiv 2310.08560), HMO (arXiv 2604.01670), externalization survey (arXiv 2604.08224).

**[PREPRINT]** Staleness via utility-weighted exponential time-decay: frequently-recalled records resist demotion as they age; low-utility records sink to archive; nothing is deleted. (HMO formula exp(−λ·Δt/ln(1+Cm)) — treat exact formula as a bet.)

**[REFUTED — do not build on]** "Hierarchical retrieval structure ALONE improves accuracy" (TiMem claims, 0-3 and 1-2). Tiering is for context budget + staleness management; don't claim retrieval-accuracy gains from hierarchy per se.

**Design implications:**
- Three tiers as files: hot snapshot (boots every session), working store (loaded on demand), append-only archive (subagent-only access).
- Demotion is scoring, not deletion; archive is append-only.

## 6. Consolidation is a verify-and-repair pipeline, not in-place rewriting
Perishability: durable · Verified: 2026-07 · Round: R2

**[PREPRINT]** MemMA pattern: after a session, synthesize probe QA pairs → test provisional memory → convert failures into repair proposals → consolidate each candidate fact via SKIP (redundant) / MERGE (complements) / INSERT (novel) against existing memory BEFORE committing. Beats strongest baseline by ~6 accuracy points (LoCoMo, GPT-4o-mini; one claim survived 2-1, resolved via raw-table inspection).
Source: MemMA (arXiv 2603.18718). Benchmark-only, no deployment evidence.

**Design implication:** the kernel's reflection/consolidation pass is proposal → verify → merge, never freeform rewriting of memory files.

## 7. Externalization is the unifying frame
Perishability: durable · Verified: 2026-07 · Round: R1

**[VERIFIED — medium; framing claim, single survey]** The field's convergent principle: progressively relocate cognitive burdens from model-internal computation into persistent, inspectable, reusable external structures — memory externalizes state, skills externalize procedure, protocols externalize interaction, harness engineering unifies them.
Source: 21-author review preprint (arXiv 2604.08224, Apr 2026).

**Design implication:** every kernel component must produce inspectable files, not implicit model behavior. This is the theoretical justification for the kernel+builder shape.

## 8. Instruction drift is real, large, and mechanistic — prompts don't hold
Perishability: perishable · Verified: 2026-07 · Round: R2

**[VERIFIED]** Average 39% performance drop across 15 LLMs (200K+ simulated conversations) when instructions arrive across underspecified turns vs. single-turn fully-specified (Laban et al., "LLMs Get Lost in Multi-Turn Conversation", ICLR 2026). Independent study: GPT-4o 96%→63% instruction-following multi-turn; small models collapse to 24–27%.
Caveat: one published critique argues the 39% magnitude is partly experimental-design artifact (extreme sharding; ablation recovered 15–20pp) — direction and mechanism robust, magnitude setting-dependent.

**[VERIFIED]** The mechanism is NOT capability or memory loss: aptitude drops ~15% while unreliability roughly DOUBLES; models lock in premature interpretations of ambiguous early input (intent-alignment gap) and rarely recover after a wrong turn (~29% recovery even for top models). "Add more context" is explicitly rejected as the fix ("Memory is not Understanding", arXiv 2602.07338); the supported fix is forcing explicit intent clarification.

**[VERIFIED — medium]** Causal evidence: force the attention channel to original instructions closed and instruction recall collapses (to 0–45% depending on architecture) vs near-100% open. Reasoning-trained models show worse adherence as outputs lengthen.

**[REFUTED — do not cite]** All specific turn-count thresholds died in verification: "turn 10–15 cliff" (0-3), "GPT-5 ~18.5-turn ceiling" (0-3), "GAR declines monotonically" (0-3), "47–58% violation convergence" (0-3), "reasoning-vs-controllability trade-off" (0-3), "tool-selection stays ≥97% while instruction-following collapses" (0-3).

**Design implications:**
- Invariants must be enforced deterministically, not by prose instructions that decay with turns.
- The builder's interview must force intent specification EARLY (premature lock-in is the failure mechanism).
- Trigger resets/re-clarification on behavioral signals (repeated failures), not turn counts — no reliable threshold exists.

## 9. Deterministic gates: hooks are the enforcement primitive
Perishability: perishable · Verified: 2026-07 · Round: R2

**[VERIFIED]** Claude Code PreToolUse hooks hard-block tool calls before execution (exit code 2 + stderr fed back, or JSON permissionDecision: deny), fire before permission-mode checks in every mode, and cannot be bypassed even by bypassPermissions / --dangerously-skip-permissions. Hooks can tighten policy but never loosen it.
Source: Anthropic hooks docs (fetched live Jul 2026). Caveat: open GitHub issues (#37210, #24327) show hook deny enforcement has had real bugs → belt-and-suspenders post-hoc validation for must-never-violate invariants, and as of the 2026-07-24 re-verification the official docs no longer state the bypassPermissions interaction explicitly (claim retained from the 2026-07-23 live-docs verification; re-verify experimentally).

**Design implication:** the kernel ships hooks for invariants (file-size caps, telemetry write-through, staleness stamps) and treats prose discipline as UX, not enforcement.

## 10. Self-improvement must be bounded by external, empirical validation
Perishability: durable · Verified: 2026-07 · Round: R2

**[VERIFIED]** Intrinsic self-correction without external feedback fails and can DEGRADE performance (GSM8K/GPT-3.5 accuracy fell monotonically across self-correction rounds: 75.9% → 75.1% → 74.7%; Huang et al., ICLR 2024). Models fail to recover from instruction mistakes ~70% of the time. The authors explicitly caution against optimism about autonomous self-improvement via self-review.

**[VERIFIED — medium]** The workable pattern (Darwin Gödel Machine): proposal-then-empirical-validation — every self-modification validated against benchmarks/tests, failures discarded — because formally proving a self-modification beneficial is "impossible in practice".
**[REFUTED — do not cite]** The claim that DGM ran under sandboxing + human oversight throughout (1-2) — the human-gate recommendation rests on the self-correction literature, not DGM's demonstrated controls.

**Design implications:**
- No self-modification lands on model self-review alone. Every change passes an external check: tests, telemetry deltas, or a human gate.
- The governor is proposal → empirical validation → apply, with discard-on-failure.

## 11. Telemetry: adopt the standard schema, don't invent one
Perishability: semi-durable · Verified: 2026-07 · Round: R3

**[VERIFIED]** OpenTelemetry GenAI semantic conventions standardize the span-attribute vocabulary for LLM operations: `gen_ai.operation.name` + `gen_ai.provider.name` (required), `gen_ai.request.model`, `gen_ai.usage.input_tokens`/`output_tokens`, `gen_ai.response.finish_reasons`, `error.type`, `gen_ai.response.time_to_first_chunk`. Tool calls have a dedicated `execute_tool` span convention (`gen_ai.tool.name` required; arguments/result opt-in). Exactly two core client metrics are standardized: operation-duration histogram and token-usage histogram.
Caveats: conventions carry **Development** (not Stable) maturity and were mid-repo-relocation during verification → pin a semconv version.
**[REFUTED — do not build on]** No standardized cache/reasoning-token sub-attributes; no first-class cost attribute (derive cost from token counts); no GenAI-specific error attribute.

**[VERIFIED]** Privacy precedent: OTel GenAI captures NO prompt content or tool arguments by default — metadata only (model, tokens, durations); content capture is explicit opt-in. Mirror this locally.

**[VERIFIED]** Practitioner schema shape (Langfuse): unit of work = top-level trace containing nested TYPED observations (Generation, Tool, Retriever, Agent, Evaluator, Guardrail — not generic log lines); trace-level context (user/session/tags) propagates automatically to every nested observation.

**Design implications:**
- events.jsonl uses OTel GenAI attribute names where they exist; ad-hoc vocabulary only for what the spec lacks (intent, outcome, friction).
- Metadata-only by default; content logging is per-system opt-in.
- Typed events, session context stamped once.

## 12. Metric contract: north star as dependent variable, inputs as levers, guardrails as OEC components
Perishability: durable · Verified: 2026-07 · Round: R3

**[VERIFIED]** A valid North Star Metric (Amplitude playbook): represents user value, is influenceable, and is a LEADING indicator — lagging metrics (MRR/ARPU-style) are disqualified. Input metrics are the independent variables moved by daily work; the north star is a dependent outcome that should NEVER be targeted directly ("If you can move your North Star directly, it's probably not a good North Star").
Caveat: playbook is marketing-adjacent — fine for framework definitions, not empirical proof NSM-driven products succeed.

**[VERIFIED]** Kohavi/Tang/Xu OEC criteria for the guardrail set: each component metric must be measurable within the evaluation period, sensitive enough to detect meaningful change, timely, causally linked to long-term goals, and iteratively refined.

**Design implications:**
- The builder's metric contract has three layers: north star (leading, value-representing, NOT directly targetable) → input metrics (what the system actually moves day to day) → guardrails (OEC-style: measurable-in-period, sensitive, timely).
- Reviews act on inputs and guardrails; the north star is watched, not chased.
- Both the leading-indicator REQUIREMENT and the construction METHOD are now VERIFIED (P18, R10): derive the leading indicator as a predictive-power-weighted *composite* of short-term signals, and validate by falsification — the Prentice test can only *reject* a proxy, never bless it, so "failing to reject" is the strongest available statement, never "validated." A proxy is never confirmed from a small own-data sample (P24 shrinkage).

## 13. Abandonment is the dominant failure mode — and it is typed, often temporary, and not always failure
Perishability: durable · Verified: 2026-07 · Round: R3

**[VERIFIED]** Four distinct lapse causes in self-tracking: forgetting, upkeep burden, intentional skipping, deliberate suspending — and lapses are often temporary, not terminal. Upkeep burden ("too much work to keep up to date") is distinct from forgetting and disproportionately kills behavior-change trackers.

**[VERIFIED]** Abandonment ≠ failure (Epstein et al., CHI 2016; 193 surveyed): six distinct quit reasons, five post-tracking perspectives. Guilt is NOT universal — it concentrates among users who started with explicit behavior-change goals (16.2% activity / 8.9% finance) and co-occurs with unsustainable tracking cost; curiosity-driven trackers feel indifference (0% guilt). Some quitters keep the learned habits — abandonment can signal diminishing returns, i.e., success.

**[VERIFIED]** Habit automaticity: median 66 days to plateau, range 18–254 (Lally et al. 2010; n=39, range is extrapolated). Fixed streak targets are poorly grounded; adoption metrics need a multi-month horizon.

**[REFUTED — do not cite]** "~45% abandon trackers within 3 months" (1-2); Endeavour Partners one-third-wearables stat (never verified).

**Design implications:**
- Telemetry models lapses as TYPED, recoverable events (forgot / upkeep / skipped / suspended), not a binary churn flag.
- The kernel's #1 anti-abandonment lever is minimizing upkeep burden — automate every write the hook can catch.
- No guilt loops: a returning user gets a "welcome back + what changed," never a broken-streak shame screen. No fixed streak mechanics.
- Reviews and self-improvement cadence calibrated in months, not weeks; a "suspend" state is first-class and honorable (systems can conclude successfully).

## 14. Elicitation: interview around artifacts; the user authors the goals
Perishability: durable · Verified: 2026-07 · Round: R4

**[VERIFIED]** Structured, artifact-based elicitation beats open-ended questioning: paper prototyping elicits the most requirements; unstructured interviews are fastest but elicit the fewest with the most redundancy (Rueda et al. 2020, 4 experiments, 167 subjects). Caveats: student subjects; some quality metrics non-significant.
**[REFUTED — do not cite]** "Prototyping also best on completeness/quality/relevance" (0-3) — the advantage is quantity/significance on requirements count, not across all quality axes.

**[PREPRINT — strong preliminary]** Users must author their own goals: LLM-authored goals score far higher on SMART criteria (d=2.26) but gut ownership (d=1.38), commitment (d=1.19), and follow-through — 46.6% of LLM-condition participants acted on 2+ goals at two weeks vs 72.8% of self-authors (Chi et al. 2026, preregistered, N=470).
**[REFUTED — do not cite]** The mediation mechanism (psychological ownership as full mediator, 0-3). Cite outcomes, not mechanism.

**[VERIFIED — medium]** Implementation intentions (if-then plans): d=.65 across 94 studies; d=.61 specifically for getting started (Gollwitzer & Sheeran 2006 meta-analysis; corroborated via secondaries, primary text not directly read). MCII overall g=.24–.34 with interactive delivery significantly outperforming document delivery (g=.465 vs .277).

**[PREPRINT — thin]** Cold-start preference elicitation: pairwise comparisons need fewer interactions than single-item questions for comparable quality; elicitation-stage selection bias compounds downstream (popularity overrepresentation).

**[BET — better-specified, R10]** Preference/goal DRIFT detection after setup. Design bet holds: re-elicit at reviews using the same artifact-based method, triggered by behavioral signals (declining input metrics, typed lapses), not calendar alone. R10 supports the *direction* — mature drift detectors (ADWIN) use a variable-size window over the data stream, not a fixed schedule — but blocks a flip to VERIFIED on two counts: the only directly-fetched drift paper (arXiv:2409.16478) is simulation-only on synthetic data, and a confounder undermines a naive "fire more triggers" rule — detectors that fire *more often* perform better because of the **retraining/refresh** effect, not because they identify drift more accurately (R10 [13], 3-0). So the governor must not conclude "more re-elicitation = better"; the `re_elicit` telemetry must separate the refresh benefit from genuine drift. Killed R10 companions — do not build on them: a universally-optimal elicitation strategy (0-3), dialogue-progression as the switch signal (0-3), plateau-not-drop detection (1-2), exploration-saturation signal (1-2), derivable window size (1-2), RL-recommender manipulation magnitudes (0-3). Specific signals/windows remain unvalidated for live agents.

**Design implications:**
- The builder interviews by SHOWING DRAFTS: propose a concrete scaffold sketch early and iterate on it, rather than long question batteries.
- Goals/north-star are typed by the user in their own words; the builder refines and structures but never authors them.
- The interview converts goals into if-then rules interactively ("when X happens, the system does Y") — these become the system's hooks and review triggers.
- Prefer pairwise choices ("A or B?") over open ratings in the interview.

## 15. Prior art: the combination is unfilled (verified for the Claude Code ecosystem; presumptive beyond it)
Perishability: perishable · Verified: 2026-07 · Round: R4

**[VERIFIED]** Every individual capability exists, scattered: mobile-spine (6-question setup interview), CCUsage (11,500+ stars; fully local offline telemetry from session JSONL — proof of demand for local-only), Bouncer (independent-model audit via Stop hook), Review-squad (multi-perspective review panels). No verified tool combines interview-driven personalization + runtime discipline + local telemetry + guarded self-improvement.

**[VERIFIED]** SuperClaude, the closest large framework: has a requirements-analyst agent for the user's PROJECTS but no onboarding interview for the framework itself, and an auto-triggered self-improvement loop with NO human gate — the exact failure mode Principle 10 warns about, live in the wild.

**Unverified after 3 rounds (treat as unknown, not absent):** Agent OS, claude-flow, Letta/Mem0/Zep, ChatGPT/Claude memory features, PKM hybrids, and all public-reception data (token-bloat complaints, config abandonment). The wshobson/agents catalog claims were refuted (1-2). Ecosystem snapshots are July 2026 and rot fast.

**Design implications:**
- Position: the integration is the product, not any single capability.
- Steal proven patterns: CCUsage's local-JSONL approach validates the telemetry design; Bouncer validates independent-model gating.
- Differentiators to lead with: the metric contract, the typed-lapse abandonment model, and the human-gated governor (vs SuperClaude's ungated loop).

## 16. Agentic failure is taxonomizable — and predominantly a design problem
Perishability: durable (taxonomy) — magnitudes semi-durable · Verified: 2026-07 · Round: R5

**[VERIFIED]** MAST is the canonical empirical failure taxonomy: 14 failure modes in 3 categories — system design issues, inter-agent misalignment, task verification — built via grounded-theory analysis of 150 traces (1,600+ trace corpus, 7 frameworks), inter-annotator kappa 0.88, peer-reviewed (NeurIPS 2025 Datasets & Benchmarks). Failure is common, not edge-case: 41–86.7% failure rates across 7 SOTA frameworks (ChatDev, MetaGPT, HyperAgent, AppWorld, AG2, Magentic-One, OpenManus) with GPT-4o/Claude-3.7 backends, and multi-agent gains over single-agent baselines are minimal.
Sources: arXiv 2503.13657 / OpenReview fAjbYBmonr (eight merged claims; seven 3-0, one 2-1).
**[PREPRINT]** HORIZON's 7-category long-horizon taxonomy (LLM-judge/human kappa 0.84 over 3,100+ trajectories across web/OS/database/embodied domains) is convergent corroboration at the long-horizon altitude; MAST stays canonical here, and the kernel's 6-tag telemetry set is an adaptation of MAST + the misalignment forms — a recorded choice, not an omission. (arXiv 2604.11978, claim [26], 3-0.)

**[VERIFIED — medium; 2-1 vote]** Failures trace predominantly to system/architecture design flaws rather than model limits, and single design fixes yield large gains with the same model and prompts: giving one agent final decision authority +9.4pp task success; adding a high-level verification step +15.6pp (ProgramDev). Caveats: "predominantly" is stronger than the paper's hedged wording; these are first-step interventions, not cures.

**[VERIFIED]** Verifier-ran is a weak signal: task-verification failures are ~21–23.5% of MAST failures — No/Incomplete Verification (FM-3.2, 8.2%) and Incorrect Verification (FM-3.3, 9.1%) — and existing verifiers often perform only superficial checks (code compiles) while passing functionally broken output (ChatDev chess example). Only the FM-3.2/3.3 percentages survived verification.

**[PREPRINT]** Agents rarely self-correct: across 20,574 real coding-agent sessions (1,639 repos, IDE+CLI), 91.49% of visible resolutions required explicit user correction; 90.50% of failure episodes cost only effort/trust (recoverable, not catastrophic). Misalignment takes 7 recurring forms, from project reading comprehension to progress reporting. (arXiv 2605.29442, all 3-0; fresh non-peer-reviewed preprint.)

**[VERIFIED]** Errors compound and self-condition over horizon length: without decomposition/error-correction, success probability decays exponentially with step count, and marginal single-step accuracy gains compound into exponential task-length gains — so single-step benchmarks mask large gaps. Self-conditioning is a distinct mechanism: a model's own prior errors in context breed further errors (controlled counterfactual at fixed context length; scaling to 200B+ doesn't eliminate it). Three independent papers converge ("Illusion of Diminishing Returns" NeurIPS 2025, MAKER arXiv 2511.09030, HORIZON arXiv 2604.11978).

**[PREPRINT]** Failures are gradual and silent, dominated by epistemic errors: 57.9% of failures in 63K+ annotated CLI coding-agent steps are knowledge/understanding errors (vs 32.8% competence), often hidden until unrecoverable. False success collapses from 45–48% of failures to 3% where something other than the agent can independently verify state (dual-control; observational, single domain). (arXiv 2607.09510, 2606.09863.)

**[REFUTED — do not build on]** MAST sub-mode percentages beyond FM-3.2/3.3: "System Design Issues largest category (44.2%), Step Repetition 15.7%, Unaware of Termination Conditions 12.4%" (0-3). "TF-IDF detectors beat LLM-judge monitors, 3,300x faster" (0-3). "75.8% of AppWorld self-assessed status claims are false success" (1-2).

**Design implications:**
- Telemetry failure_mode tags (SP3) use MAST's category level plus FM-3.2/3.3; other mode-level percentages need per-figure re-verification before citing.
- Correction loops are external by design — a human or an independent check, never agent self-review (converges with P10).
- Verifiers must record WHAT they checked against the task objective; "a verifier ran" is not evidence. Prefer designs where something other than the agent can verify state.
- Error-in-context is a leading indicator of further errors → checkpoint/reset after detected mistakes.

## 17. The capability frontier is probed, never recalled
Perishability: perishable · Verified: 2026-07 · Round: R5

**[VERIFIED]** Capability ≠ reliability: probe with pass^k (ALL k trials succeed), never pass@k (any of k). On tau-bench, GPT-4o-based agents succeeded on <50% of tasks single-trial, but consistency across 8 repeats (pass^8) fell below 25% in the retail domain. (ICLR 2025, 3-0.) Caveat: GPT-4o-era (mid-2024) figures — the phenomenon persists in tau2/tau3 successors, the numbers do not transfer to current models.

**[VERIFIED — medium]** METR time horizons are 50% coin-flip thresholds, not completion guarantees: the 80%-horizon is roughly 4–5x shorter for the same model (Claude 3.7 Sonnet: ~50 min at 50%). The ~7-month doubling trend passed 2-1 with a methodological critique on record (sparse data points, METR's own 1–4 doublings/year band, two-lab model concentration) — cite with error bars, never as a precise law; two adjacent framings of the same data were refuted in verification.
Sources: metr.org/time-horizons, arXiv 2503.14499, METR "Time Horizon 1.1" (Jan 2026).

**[PREPRINT]** Long-horizon difficulty is domain-structural, not human-duration-estimated: reliability decay is domain-stratified (software-engineering GDS drops 0.90→0.44 across the duration range while document-processing stays nearly flat, 0.74→0.71), and collapse thresholds differ sharply by domain (web agents collapse at small compositional depth; OS/database sustain longer). A duration-based capability estimate from another domain does not transfer. (arXiv 2603.29231 2-1 + HORIZON 3-0; both preprints, convergent.)

**[PREPRINT]** Cheap pilots work: estimate per-step success rate p on a small random subset of steps with repeated trials across multiple models before committing to a design (MAKER's recommended method). Empirically: a 19-task, 12-model, 1,368-episode pilot cost $4.26 total and surfaced real failure modes (quota exhaustion inflating apparent pass@1 by up to 15%, dead provider endpoints, missing cost circuit-breakers) before a 23,392-episode study that itself cost $80–120. (arXiv 2511.09030, 2603.29231; both 3-0.)

**[REFUTED — do not cite]** "Near-100% success on short tasks but under 10% beyond ~4 human-hours" (0-3); "12B Mistral Nemo beat 400B Llama 4 Maverick on long-horizon reliability" rank inversion (0-3); "a 1% per-step error rate fails at ~100 steps" (0-3); METR exponential-fit and 7-month-doubling-as-law framings (both 1-2).

**Design implications:**
- Frontier claims carry short refresh windows: every "the model can do X" is a dated claim, re-probed, never recalled from doctrine.
- The builder runs a small pass^k probe — multi-trial, multi-model, in the actual target domain — before committing a design to "the model can do X" (SP3).
- Probe results land in the manifest as dated claims with pass^k numbers, not booleans.

## 18. Objectives corrupt under optimization — design for the four mechanisms
Perishability: durable · Verified: 2026-07 · Round: R7

**[VERIFIED]** Goodhart failure is four mechanistically distinct modes — regressional, extremal, causal, adversarial — each needing a different mitigation; one generic fix ("just add a guardrail") cannot cover all four. Verified specifics: regressional — proxy = goal + noise, so extreme proxy values systematically overselect noise; extremal — proxy-goal correlations validated in-distribution silently break exactly at the extremes optimization pushes toward; causal — intervening on a non-causally-correlated proxy fails to move the goal. Therefore every input lever must be causally validated, and metric behavior at extremes cannot be assumed from normal-range behavior.
Sources: Manheim & Garrabrant (arXiv 1803.04585) + MIRI summary; 3-0 votes across eight merged claims. The standalone adversarial-variant definition failed verbatim verification (0-3) — the four-way taxonomy including it is confirmed; the folk phrasing is not.

**[VERIFIED]** Severity scales with optimization power — verbatim from the primary source: "the increased optimization power offered by artificial intelligence makes it especially critical for that field." Agentic systems are the worst case, not an edge case. (3-0, x2 merged.)

**[VERIFIED — medium; 2-1]** No metric contract is permanently Goodhart-proof: Skalse et al. (NeurIPS 2022, arXiv 2209.13085) proved a proxy reward is unhackable relative to a true objective only in the degenerate case where one reward function is constant (scoped to all stochastic policies). Scheduled proxy revalidation is a lifecycle event, not one-time hardening.

**[PREPRINT]** LM agents specification-game zero-shot, with no task-specific training (Boat Race observed-vs-hidden reward 48.42 vs 12.66, Qwen3-235B-Thinking), and RL training amplifies rather than fixes it: capable models lock into locally-rewarding exploits before discovering the safe policy — an exploration failure caused by competence itself — persisting across 1.5B–14B scales; credit assignment, exploration prompts, longer context, and entropy regularization all failed. (arXiv 2606.15385; 3-0 votes but ~1 month old, text gridworlds, RL at ≤14B — mechanistic evidence, not frontier-scale proof.)

**[VERIFIED]** North-star non-actionability is now mechanism-backed, not folklore: Amplitude designs the north star as a non-directly-movable dependent outcome ("If you can move your North Star directly, it's probably not a good North Star") over 3–5 causally-workable input levers — the structural anti-gaming defense P12 already encodes. Wells Fargo is the canonical quantified organizational failure: cross-sell quota pressure → millions of fake accounts, $3B in penalties, and active CONCEALMENT of the metric-goal gap (PINs set to "0000", employees' own contact info on applications) — "surrogation", the metric substituting for the goal. Diversification raises gaming cost: Clifford Chance replaced single billable-hours with seven bonus criteria (news coverage says five–six; count approximate), SoftBank spread metrics across three time horizons (Thomas & Uminsky, Patterns 2022).

**[VERIFIED — medium; single practitioner blog]** The goal itself lives above the metric layer: a short strategic narrative that multiple metrics serve as evidence for, since single-number north stars still trigger Goodhart ("people optimize for the metric, rather than the value it's supposed to represent" — Mehta, ex-CPO Tinder).

**[VERIFIED — R10; construction method settled]** A valid leading indicator is **derived, not guessed** — the surrogate index is the predicted value of the lagging north-star given the short-term surrogates. Linear case: multiply each surrogate's estimated treatment effect by its regression coefficient on the primary outcome — objective predictive-power weighting replacing intuition (Athey-Chetty-Imbens-Kang, NBER w26463; Google "Choosing a Proxy Metric from Past Experiments", KDD'24). Compose *multiple* qualitatively-distinct short-term signals into ONE index rather than betting on a single leading indicator; the composite maps onto Sharpe-ratio portfolio optimization (convex QP) that de-weights correlated proxies; the optimal weighting is sample-size-dependent. Three named failure conditions the doctrine encodes as guardrails: (a) **Prentice's 4th criterion is asymmetric** — it can only *reject* a poor surrogate, never affirmatively *validate* a good one (failing to reject ≠ validity; reformulate as an equivalence test to claim validation); (b) **surrogate paradox** — a proxy can harm a subgroup on the true outcome even when population checks and Prentice hold, so only the "strong" surrogate (treatment affects the outcome *only* through the surrogate) excludes it assumption-free; (c) **sample-size floor** — a single small dataset cannot credibly validate a surrogate; validation needs large or pooled/meta-analytic data. (R10: 12 claims, all 3-0 except two 2-1; primary sources — Athey w26463, Alonso et al. Prentice re-examination, Ma/Yin/Liu/Geng individual surrogate paradox, Buyse-Molenberghs meta-analytic validation.)

**Cairn applies the discipline, not the literal estimator.** A single personal instance has no experimental+observational two-sample setup, so the builder cannot run the surrogate-index regression at build time. What is VERIFIED and usable is the *construction discipline*: compose don't bet-on-one; weight by predictive power and de-weight correlated proxies; **falsify never confirm** (frame the P18 causal-validity check as an attempt to *reject* each candidate — "failing to reject" is the strongest available statement, never "validated"); and never treat a proxy as confirmed from a small own-data sample — confirmation waits on accumulated data, which is exactly P24's shrinkage handover.

**[REFUTED — do not build on]** Pre-R10 canonical methods that died: "behavior-measuring proxies beat stated-intent proxies (NPS as referral stand-in)" (1-2) and "build a leading-indicator chain by backward-chaining from a lagging outcome, each step demonstrably predictive of the next" (0-3). Also: "every success metric must be paired with a counter-metric" as a universal rule (1-2 — continuous guardrail monitoring itself is verified and already in P12); Wells Fargo cross-sell-metric specifics ("~3.5M accounts, sole metric, no guardrails", 0-3) — cite the verified $3B/concealment version above. R10 additions: "Prentice's classical criterion by itself rules out the surrogate paradox" (0-3 — it does not; it lacks transportability) and "the surrogate paradox cannot occur when both ACE(T→S) and ACE(S→Y) are positive" (0-3 — it still can).

**Design implications:**
- The governor runs a scheduled proxy-revalidation sweep (SP3): every proxy-goal link in the metric contract is a dated, testable claim re-checked over time — extremal Goodhart decouples proxies precisely where optimization pushes.
- The builder's metric-contract interview cites mechanisms, not folklore: each input lever gets a causal-validity check (framed as falsification per R10 — try to *reject* it), each metric an extreme-range question, and audits look for concealment, not just drift. The north-star proxy is derived as a predictive-power-weighted composite of short-term signals, never a single bet.
- Extends P12: watched-not-chased is not taste — it is the structural mitigation for Goodhart under agentic optimization power, and it needs the revalidation lifecycle above because no static contract stays safe.

## 19. Autonomy is graded by blast radius; asks are a budget
Perishability: durable · Verified: 2026-07 · Round: R8

**[VERIFIED]** Humans are structurally bad at sustained oversight of reliable automation: failure detection was 33% under constant-reliability automation vs 82% under variable reliability — a 149% difference — though the same malfunctions were caught ~97% single-task (Parasuraman & Manzey 2010, reproducing Parasuraman/Molloy/Singh 1993; replicated). Expertise and practice do NOT fix it — pilots and controllers show the effect too (one merged claim 2-1). Automation bias hits competent professionals: erroneous advice followed at RR 1.26 (95% CI 1.11–1.44), and users reversed their own CORRECT decisions for wrong system advice in 6–11% of cases (Goddard et al., JAMIA systematic review).
**[REFUTED — do not cite]** "Complacency appears ONLY under multi-task load" (0-3); "moderate ~70% reliability is optimal for monitoring" (1-2).

**[VERIFIED]** Uniform per-action gating rubber-stamps in practice: users approved ~93% of Claude Code permission prompts — Anthropic's own first-party telemetry, framed by Anthropic as approval fatigue, not review. Their stated alternative grades containment by likelihood-of-failure × damage (blast radius), not uniform human-in-the-loop.
**[REFUTED — do not cite]** The companion mechanism claim, "auto mode + OS sandboxing cut prompts 84%" (0-3) — cite only the 93% figure and the two-factor risk framework.

**[VERIFIED]** Oversight fails via TWO identifiable modes, and rubber-stamping is only one of them: "Either humans act as rubber stamps, approving AI outputs they do not fully understand, or systems are constrained so tightly that AI collapses into rule-following automation" — over-constraint leaves nothing real to oversee. And transparency is not the cure: "explanations alone rarely fix inappropriate reliance," while "interventions that change the interaction (e.g., who decides, when, and with what friction) tend to help more." (Zhu et al., CSIRO Data61, AI and Ethics 2026, peer-reviewed; 3-0, 3-0, 3-0 — three merged claims; corroborated by XAI-reliance literature, arXiv 2403.09552, 2502.13321.)

**[VERIFIED]** The graded structure is Horvitz (CHI 1999): act/ask/do-nothing as an expected-utility computation over four outcomes with TWO thresholds (inaction/dialog and dialog/action) that shift with context — rising when the user is absorbed, falling when rushed. **[PREPRINT]** Feng et al. 2025 (arXiv 2506.12469) define five autonomy levels by the USER's role (operator → collaborator → consultant → approver → observer) and flag L4 approver rubber-stamping — including misaligned agents exploiting user disengagement to gain autonomy — as open and unsolved.
**[REFUTED — do not cite]** "Horvitz ties action COST to the threshold" (0-3) — the verified threshold-shifters are attention depth and time pressure; the blast-radius link comes from Anthropic's framework, not Horvitz.

**[VERIFIED — medium; two of three claims 2-1]** Ask FREQUENCY drives abandonment: prompting on every visit vs 25% of visits worsened retention (HR 0.78, p=0.003) even though each prompt took a median 1.55 seconds — frequency, not per-decision cost, burns users out. Users prefer deferred re-commitment ("not now, ask later") over permanently locking in an easier setting. (Kovacs et al., CHI 2021 randomized experiment, 8,000+ users. Caveats: dose-response not monotonic — occasional beats constant, never-asking wasn't better; single browsing-nudge case study, not an AI agent.)

**[VERIFIED — direction only; R10]** The per-additional-ask harm gradient is real: clinical alert acceptance dropped **~30% for each additional alert per encounter** (negative-binomial IRR ≈ 0.70, p<.001; Weiner et al. 2017, 1.26M advisories + 326K drug alerts, 112 clinicians) — genuine within-session concurrent-burden dose-response, corroborating Kovacs. But it is cross-domain (clinical decision support), measures acceptance decline not abandonment, and the same study found NO longitudinal desensitization for newly-deployed alerts. There is no published asks-per-session → abandonment curve for a long-lived conversational assistant, so **the ask_budget default of 1 stays a defensible BET** — a conservative floor justified because per-additional-ask harm rises steeply in every adjacent literature. The exact number awaits first-party in-domain telemetry (which P24's shrinkage can eventually tune). **[REFUTED — do not build on]** "Once a user overrides an alert once they override repeats 87.9%/99.9% of the time — near-deterministic habituation lock-in" (0-3): there is no override-lock-in mechanism to lean on.

**[VERIFIED]** When an ask IS spent on a genuinely risky action, make it inhibitive: forcing interaction (type/swipe/delay) before the risky choice is possible cut unsafe choices by up to 50%, was 2–3x better at surfacing new critical information under extreme habituation, and the active variants (Swipe, Type) stayed effective after many exposures while passive attention-directing designs decayed; interstitial warnings were bypassed 45% vs 82.5% for passive contextual ones. (Bravo-Lillo et al. SOUPS 2013/2014, Kaiser et al. USENIX Security 2021; MTurk lab settings — transfer to agent confirmation UIs is inferential.)

**[VERIFIED]** A small, even token, override channel largely cures algorithm aversion: adoption of an imperfect-but-superior model jumped from 32% (unmodifiable) to 73–76% (adjustable), and shrinking the allowed adjustment by 80% changed nothing (71%/71%/68%, p=.809) — people need a nonzero channel, not discretionary power (Dietvorst, Simmons & Massey, Management Science 2018). The underlying aversion: one visible algorithm error costs disproportionate trust — asymmetric confidence updating, algorithm errors damaging confidence in all four studies, human errors in only one, despite humans making 15–97% more error (JEP: General 2015; replication limits — treat as a first-exposure effect, not a universal law).

**[VERIFIED — one claim 3-0, two 2-1]** Where effective oversight cannot actually be performed, mandating it is theater: across 41 government-algorithm oversight policies, people are structurally unable to perform the assumed functions, so the mandates legitimize flawed systems, create a false sense of security, and function as liability shields (Green, Computer Law & Security Review 2022; evidence base is government algorithmic decision-making).

**Design implications:**
- Every instance carries an ask-budget and a blast-radius table (SP3): asks are a rationed resource spent only where load-bearing; per action class, act/ask/do-nothing is set by likelihood-of-failure × blast radius, never uniform per-action gating.
- Irreversible + externally-visible actions are never autonomous — and their gate is inhibitive (forced interaction with the consequential element), never a passive confirm dialog.
- Always leave a user-editable override knob, even token-sized, including when telemetry says the default is right — the channel's existence, not its width, buys adoption.
- Over-constraint is the failure on the other side of rubber-stamping: an autonomy table that puts everything in `ask`/`never` collapses the agent into rule-following automation with nothing real to oversee. And when telemetry shows miscalibrated trust, change the interaction (who decides, when, with what friction), not the explanation text.
- "A human approved it" is not evidence of review (converges with P16's "a verifier ran"). Extends P13: ask friction spends the same budget upkeep burden does — trust & adoption fold in here, and rationing asks is an anti-abandonment lever.

## 20. Default single-threaded; fan-out is bought with tokens
Perishability: semi-durable · Verified: 2026-07 · Round: R9

**[VERIFIED]** The complexity ladder: direct model call → single agent with tools → multi-agent orchestration. Take the lowest rung that reliably works and escalate only when measurement shows context limits, parallelism needs, or specialization gains justify the coordination cost — "decision-making and flow-control overhead often exceed the benefits of breaking the task into multiple agents"; single-agent-with-tools is the stated default.
Sources: Microsoft Azure Architecture Center (updated 2026-05; 3-0, 2-1) + independent practitioner corroboration (3-0).

**[VERIFIED]** Multi-agent pays off on research-shaped breadth, and the premium IS the mechanism: Anthropic's Opus-4-lead + Sonnet-4-subagent system beat single-agent Opus 4 by 90.2% on their internal research eval — but agents use ~4x and multi-agent ~15x the tokens of a chat interaction, token usage alone explained 80% of performance variance (3 factors: 95%), and upgrading the model beat doubling the token budget. Fan-out is parallel token spend, not architectural magic; the task's value must cover the bill. Fit: heavy parallelization, information exceeding one context window, many complex tool surfaces. Coding is explicitly a poor fit — fewer truly parallelizable subtasks, and agents aren't yet good at real-time delegation. (Anthropic engineering post, first-party; 3-0 x3, 2-1. Scoped "in our data" — one deployment context, not a universal law.)

**[VERIFIED — medium; practitioner doctrine, not benchmarked]** The single-writer principle: parallel multi-agent writes fail because context isn't shared thoroughly enough and independent actions carry implicit decisions that conflict — so readers/advisors/reviewers may be many, but write/action authority stays with ONE agent. (Cognition "Don't Build Multi-Agents" + 2026 follow-up, which narrows rather than retracts; 2-1, 3-0.) Extends P3: condensed-return fan-out is for reads and analysis; writes never fan out.

**[VERIFIED — medium; single official doc, 3-0 x2]** Subagent delegation criteria (LangChain deepagents docs): DO delegate multi-step tasks that would clutter main context, specialized domains needing custom instructions/tools, tasks needing different model capabilities, and to keep the main agent on high-level coordination. DON'T delegate simple single-step tasks, tasks needing maintained intermediate context, or where delegation overhead outweighs the benefit.

**[VERIFIED]** Cascade routing — cheap model first, confidence-gated escalation — is the strongest-evidenced cost lever: FrugalGPT matched GPT-4 accuracy at 50–98% cost reduction (98.3% finance headlines, 73.3% legal, 59.2% reading comprehension — savings are domain-dependent) or beat GPT-4 by up to 4% at equal cost; a GPT-J → J1-Large → GPT-4 cascade hit 0.872 accuracy vs GPT-4's 0.857 at $6.5 vs $33.1. (Stanford, TMLR 2024 peer-reviewed; 3-0 x4, 2-1. 2023 dollar figures are stale — carry the structure, not the prices.) **[PREPRINT]** Modern two-stage cascades stay within ~1–2pp of the strongest model with the cheap model absorbing ~59% of queries; the escalation classifier and confidence calibration are where the value is. (2026 preprints, narrow benchmarks; 2-1 x2, 3-0 x2.)

**[PREPRINT]** Quality beats diversity in cheap-model swarms: best-of-n repeated sampling from the single best model (Self-MoA) beats mixing diverse models by 6.6pp on AlpacaEval 2.0 (65.7 vs 59.1 LC win rate) and 3.8% average across MMLU/CRUX/MATH; regression shows output quality dominates diversity (α > β on all datasets, p<0.001) — mixing in weaker models for diversity actively hurts. (Self-MoA arXiv 2502.00674, preprint-only rebuttal of the peer-reviewed ICLR 2025 MoA result; 3-0 x3, 2-1 x2.)

**[VERIFIED]** Two-model consistency-switching (ModelSwitch): repeated-sample two comparable cheap models, stop when their answers agree — matches or beats single-model self-consistency at ~34% fewer samples on average (81% on MATH with 35 samples vs Gemini 1.5 Flash's 79.8% at 512), and beats debate/judge topologies outright on MMLU-Pro: 63.2% vs MAD 45%, AgentVerse 38%, ChatEval 43%, MoA 50.8% at a unified budget. No verified positive case for debate/judge panels survived R9 at all. (AAAI 2026 peer-reviewed; 3-0 x2, 2-1. Caveat: debate baselines author-reproduced; the stronger multi-LLM MAD variant, 50.2%, was omitted from the headline — 63.2% still clears it.)

**[REFUTED — do not build on]** The folk numbers died wholesale: "open-source heterogeneous swarm beats GPT-4o by a large margin" (0-3); topology token multipliers "fan-out costs 4-5x, swarm 2-10x" (0-3); "orchestrator + cheap task-specific workers cuts costs 40-60%" (0-3) and "Microsoft recommends per-agent model tiering" (0-3) — cross-agent tiering as vendor-prescribed guidance currently has NO verified source, even though cascade economics support the idea; "Princeton study: single agent matched multi-agent on 64% of tasks" (0-3); "40% of multi-agent pilots fail within six months" (0-3).

**Design implications:**
- The builder's orchestration selector (SP3) encodes the ladder + cascade, not the folk version: default single agent with tools, escalate only on measured evidence, multi-agent reserved for research-shaped breadth whose value covers ~15x tokens.
- Side-effectful work is single-writer by construction: spawn readers/advisors freely (P3's condensed-return fan-out), never parallel write authority.
- When buying redundancy, prefer best-of-n from the strongest affordable model or a 2-model consistency switch over heterogeneous swarms or debate panels.

## 21. Judges are instruments — rubric-first, calibrated, probabilistic
Perishability: durable (methods) — magnitudes semi-durable · Verified: 2026-07 · Round: R6

**[VERIFIED]** The rubric is the highest-leverage judge input — explicit evaluation criteria matter more than reference answers: removing the criteria drops GPT-4o's human correlation 0.666→0.591 vs 0.638 for removing the reference; both together are needed, and weaker judges degrade more (LLaMA3.1-70B: 0.641→0.555/0.581). For 1–5 scales, describing only the extreme scores (1 and 5) yields the highest human alignment — intermediate descriptions add little. (Yamauchi et al., ACL 2026 GEM / arXiv 2506.13639; 3-0 votes. Scoped to BIGGEN-Bench with two evaluator models — documented findings, not universal laws.)

**[VERIFIED]** Judge nondeterminism is an asset if sampled and averaged, not a bug to suppress at temperature 0: sampled decoding with multiple scored samples beats greedy, and mean aggregation beats majority vote and median consistently across evaluators and settings (GPT-4o: greedy 0.635 vs mean 0.666). (Same paper; 3-0.)

**[VERIFIED]** CoT adds little ONCE the rubric is good: with well-defined score descriptions already in the prompt, direct scoring performs comparably — rubric investment beats reasoning-trace investment. The conditionality is load-bearing: **[REFUTED — do not cite]** the unscoped version ("judge CoT adds negligible reliability" without the good-rubric condition) died 0-3 — CoT does help when criteria are missing.

**[VERIFIED]** Judges import documented cognitive biases: position (prefer the first option in pairwise), verbosity (longer rated higher regardless of quality), self-preference (own model family rated higher — quantified for GPT-4, arXiv 2410.21819), and sycophancy (favoring confidently-stated or bias-confirming answers even when wrong). The existence of these biases is solid; precise magnitudes are not. **[REFUTED — do not cite]** "position bias swings 10–15 points" (0-3); "reordering swings judge agreement by 25pp" (0-3); "self-preference tracks perplexity, not self-recognition" (0-3); "binary pass/fail rubrics beat 1–5 Likert scales" (1-2 — common practitioner advice with no surviving evidence).

**[VERIFIED — medium; 2-1, practitioner-corroborated]** Judge prompts are not reliable out of the box: they need iterative calibration against human expert judgments before being trusted, and show inconsistent strictness and overconfidence when rubrics are underspecified. **[PREPRINT]** Even ensembles only reach moderate reliability: a 3-model majority ensemble (GPT-4o, Gemini-2.5-Flash, GPT-4o-mini) hit kappa 0.432 (95% CI [0.239, 0.622]) against 100 human labels — below the 0.60 "substantial" bar — with a systematic conservative skew (25% of traces marked correct vs 38% by humans); naive substring matching is chance-level (kappa 0.049). The fix is a calibration transform: report P(human=correct|judge=correct)=0.76 and P(human=correct|judge=wrong)=0.25, never raw verdicts. (AgentProp-Bench, arXiv 2604.16706; 3-0 votes, but single-author unreviewed preprint, n=100 single-annotator labels, wide CIs.)

**[PREPRINT]** Agent evaluation must decompose to trajectory/stage level: an injected parameter-level fault propagates to a wrong final answer with human-calibrated probability ≈0.62 (range 0.46–0.73 across models), and a single end-to-end outcome metric cannot localize where the pipeline failed. (Same preprint; the stage-decomposition argument survived 3-0, an unhedged variant of the 62% figure was separately refuted 1-2.) **[VERIFIED]** The tooling tradeoff (LangSmith/AgentEvals docs): deterministic trajectory-match evaluators are fast, cheap, and deterministic for well-defined workflows; LLM-judge trajectory evaluators buy qualitative assessment (efficiency, appropriateness) at the cost of an LLM call and nondeterminism.

**[VERIFIED]** For binary verdicts, report Cohen's kappa plus one correlation figure and nothing more: Pearson's r, Spearman's rho, Kendall's tau-b, phi, and MCC all collapse to a single identical value on non-degenerate binary data; kappa is the only common coefficient that adds information. (arXiv 2606.00093; mathematical identity, independently confirmed numerically — not time-sensitive.)

**Design implications:**
- Judge-building starts at the rubric: explicit criteria + reference answer, extremes-only score descriptions, sampled scoring with mean aggregation — before any thought of fancier judges.
- An instance that builds a judge owes a human-labeled calibration set — an ask-budget expense (P19) — and stores verdicts as P(correct) via the calibration transform, never as ground truth.
- Default to deterministic trajectory checks; escalate to LLM judges only for qualitative criteria — and evaluate stages, not just outcomes, or failures can't be localized.
- Verifiers must record WHAT they checked against the task objective (ties to P16's "a verifier ran is not evidence").

## 22. Knowledge expires on events, not clocks — and models can't feel it
Perishability: durable · Verified: 2026-07 · Round: R6

**[VERIFIED]** The living-systematic-review (LSR) discipline is the canonical model for knowledge that must not rot: continual surveillance via ongoing pre-specified searches with timely incorporation, as distinct from one-off static publication — with a hard bound that new evidence be incorporated within a maximum of six months of becoming available (an upper limit expected to shrink). (Elliott et al. 2017, J Clin Epidemiol — foundational Cochrane methods paper, triangulated across Cochrane/AHRQ/F1000Research; 3-0.)

**[VERIFIED]** Living mode has entry AND exit criteria — maintain a refresh loop only while all three hold: (1) the topic is a decision-making priority, (2) certainty in existing knowledge is low/very low, (3) new evidence is likely to emerge — and exit to static mode when any fails. A checkable per-entry rule for which cached knowledge deserves surveillance at all. (Elliott et al. 2017 + living-guideline follow-up; 3-0.)

**[VERIFIED]** Re-verification is event-triggered, not clock-driven. Each surveillance pass has three outcomes: no new evidence → do nothing; new evidence that doesn't change conclusions → lightweight note; new evidence that changes conclusions or expands scope → full update. Mature LSRs also trigger on external events — a policy change (an FDA Emergency Use Authorization prompted an update) or completion of specific high-value studies (platform trials) — not calendar rules. (F1000Research + Cochrane case studies; core rule 3-0, external-event examples 2-1.)

**[VERIFIED]** Cheap continuous surveillance is decoupled from expensive re-verification: over ~30 monthly search cycles, a Cochrane LSR published only 3 full updates — roughly 90% of surveillance passes found nothing warranting re-publication. The sustainable pattern is frequent low-cost checks gating rare high-cost refreshes.

**[VERIFIED]** Two guardrails bound the event model: there is no universal quantitative staleness threshold (cadence depends on topic evolution, evidence volume, and capacity) — but a hard ceiling regardless: no living review goes longer than one year without a full re-review, even if zero new evidence was found, specifically as a check that living status and cadence are still warranted. Caveat: all cadence numbers are from medical evidence synthesis; applying them to technical knowledge is analogy — compress the windows for fast-moving domains.

**[PREPRINT]** Models cannot self-detect stale knowledge: on the STALE benchmark the strongest model (Gemini-3.1-pro) scored only 55.2% overall at recognizing stale memories — near coinflip — with a reproducible explicit/implicit gap: 92.0% when asked directly whether a fact still holds, 30.0% when the query merely presupposes the stale state (some models drop 76%→4%). The useful staleness framing is structural, not temporal: "Implicit Conflict" — a later observation invalidating an earlier memory with no negation cue — split into Type I (same-attribute conflict) and Type II (an upstream change cascading through a dependency chain). (arXiv 2605.06527, 400 expert-validated scenarios, 1,200 queries; the gap 3-0, the 55.2% headline 2-1; unreviewed May 2026 preprint.)

**[PREPRINT]** The same discipline framed for agent evals: static point-in-time evaluation is a "compliance fiction" — the illusion that a system evaluated at t0 remains compliant at t0+n; the alternative is a governed lifecycle with continuous score monitoring and automatic quarantine on drift. (arXiv 2605.24737; 3-0 as a characterization of the paper's argument; small unreviewed study.)

**[REFUTED — do not build on]** "Cosine-similarity staleness detection is structurally infeasible (AUROC 0.59, near chance)" (0-3) and "a deterministic supersession/versioning layer drives RAG stale-fact serving from 15–40% to ~0%" (1-2) — neither embedding-similarity pessimism nor the supersession fix has surviving evidence; automated propagation-invalidation at knowledge-base scale is an open question.

**Design implications:**
- Expiry triggers must be structural — dated claims, dependency graphs, census diffs — never model self-assessment; staleness probes ask explicitly ("is X still true?"), because prompts that presuppose a stale fact are exactly where models comply with it.
- doctrine_write's Refresh-by dates in each instance's docs/RESEARCH.md are the structural triggers the governor's expiry sweep (SP3) reads as the cheap surveillance pass, escalating to full re-research only when new evidence changes conclusions — with an unconditional annual-ceiling audit of every entry. The annotations in THIS file are swept by a different mechanism: the repo's test suite fails on any principle Verified >12 months ago (the same annual ceiling) or any perishable principle >6 months old.
- Refresh loops are rationed by the entry/exit criteria: decision priority × low certainty × likely new evidence; anything failing them goes static.
- By this principle's own logic, R6's judge magnitudes carry their own re-verification triggers — hence P21's semi-durable magnitudes.

## 23. Mechanism selection: context cost first, then the decision tree
Perishability: perishable · Verified: 2026-07 · Round: docs-verified (claude-code-guide)

**[VERIFIED — first-party docs]** The first question for any new capability is context cost: resident (CLAUDE.md is fully loaded every session; each MCP server holds ~100–120 tokens of tool list) vs on-demand (skills, subagents, saved workflows load only when used). Resident tokens are P1's distractors — default to on-demand.

**[VERIFIED — first-party docs]** Given the cost class, the selection tree:
- Fires automatically on an event, no judgment call → hook (deterministic; P9's enforcement primitive).
- Reusable procedure requiring judgment → skill (on-demand; subsumes legacy slash commands).
- Context-bloating side task → subagent (isolated window; P3's condensed-return fan-out).
- More than a handful of agents, or multi-stage verification → saved workflow (state lives in script vars, outside model context).
- An external system is the source of truth → MCP server.
- Facts every session genuinely needs → CLAUDE.md (and nothing regenerable).
- Distribution/versioning of any of the above → plugin.

**[VERIFIED — first-party docs]** Census enumerability is asymmetric: MCP servers are enumerable (`claude mcp list` / `system-init` array), but tool schemas are not programmatically queryable and no registry-search API exists — so the builder census infers capability from server identity, and rung 2 of the data-access ladder ("a connector exists but isn't installed") is a manual-assisted web-lookup + user-approval flow, never automatic.

Detail file: `docs/research/research-mechanisms-claude-code-2026-07.md` (full selection matrix, hook-event surface, plugin packaging limits; docs-verified 2026-07-23, re-verified 2026-07-24) — refresh-by next release or any Claude Code minor-version jump; this principle expires with it.

Recorded deviation: the tree says skills subsume legacy slash commands, yet scaffolded instances ship `commands/*.md`. Deliberate — instance commands are parameter-rendered per instance at scaffold time, and per-instance rendering is what the command path supports; migrating them to skills is a kernel-release matter, not an instance fix.

## 24. Cold start: doctrine governs until instance data earns authority — continuously, by earned precision
Perishability: durable · Verified: 2026-07 · Round: R10

**[VERIFIED]** The handover from inherited doctrine to instance telemetry is **not a fixed checkpoint** — it is continuous empirical-Bayes / James-Stein shrinkage, and the "first governor review" flip is **[REFUTED — do not build on]** as the mechanism (it was the pre-R10 bet). The posterior governing any sample-estimated default is a precision-weighted blend of the doctrine prior and the instance's own telemetry: own-data weight = n / (n₀ + n) = τ² / (τ² + se²), where n₀ is the doctrine default's implicit sample size (the "authority" it carries) and n is accumulated own-data. The weight rises smoothly toward 1 as the instance's own-data variance falls below the prior's — the literal "data earns authority" formula, no threshold event. James-Stein estimates the shrinkage from the data itself (1 − (p−2)/‖X‖²), needing no preset threshold; empirically shrinkage cut prediction error >3× versus raw own-data, pulling estimates 78% toward the prior even at a non-trivial per-unit sample.
Sources: Efron 2021 (Empirical Bayes: Concepts and Methods) + Hoff (Duke, Shrinkage and Empirical Bayes); R10, all 5 claims 3-0.

**A fresh instance still starts on inherited defaults** — level-zero supplies the ask-budget and blast-radius table (P19), single-writer orchestration (P20), and the metric-contract shape (P12/P18); the build-time research round supplies whatever domain claims it verified. What R10 settles is *how control shifts off them*: per-default and gradually, by earned precision, not one global review event.

**Implementation (python3-stdlib, no stats engine): discretize the shrinkage into a per-default rule.** Each doctrine default carries an implicit sample size **n₀** (a small integer — its earned authority); a telemetry-cited proposal's own-data weight is `n / (n₀ + n)` where `n` is the count of relevant own-data events. Control shifts for that specific default when **`n ≥ n₀`** — the instance's telemetry then carries majority weight and may outrank generic doctrine. Below that, doctrine dominates. Default **n₀ = 5** relevant events; the *mechanism* is VERIFIED, the *calibration of n₀ per metric* is the residual open knob (BET, carried in the R10 ledger). The invariants (hooks, caps, privacy, the metric contract itself) never hand over — they are not sample-estimated defaults. The review skill implements this (Stage 4.5 telemetry-handover rule). Settling telemetry, named: `re_elicit` outcomes (Stage 3 goal-drift check) and post-handover proposal outcomes (adopted vs reverted rates) keep tuning n₀.

---

## Research provenance

4 deep-research rounds, ~415 subagents, ~20.6M subagent tokens, July 19 2026.
R1 context/memory (19/25 claims confirmed) · R2 enforcement/self-improvement (16/25) · R3 telemetry/metrics/abandonment (11 findings) · R4 elicitation/prior art (7 findings).
Raw outputs: research-round{1..4}-*.json alongside this file. 21+ claims refuted across rounds are listed inline — they are load-bearing negatives; do not resurrect them.

5 further rounds, 861 agent calls total, 3-vote adversarial verification, July 23 2026:
R5 failure/capability (177 agents, 32 confirmed / 13 killed, research-round5-failure-capability.json) · R6 verification/epistemics (163 agents, 36 confirmed / 9 killed, research-round6-verification-epistemics.json) · R7 objective design/Goodhart (171 agents, 30 confirmed / 15 killed, research-round7-objective-design-goodhart.json) · R8 human-agent boundary (181 agents, 34 confirmed / 11 killed, research-round8-human-agent-boundary.json) · R9 orchestration/tiering (169 agents, 30 confirmed / 15 killed, research-round9-orchestration-tiering.json).
Mechanisms reference: research-mechanisms-claude-code-2026-07.md — docs-verified against official Claude Code documentation by a claude-code-guide agent, 2026-07-23 (first-party docs, no adversarial round; carries its own refresh-by convention).

1 gaps-ledger closeout round, 175 agent calls, 7 angles, 3-vote adversarial verification, July 24 2026:
R10 five ranked candidates (45 claims verified / 33 confirmed / 12 killed, research-round10-gaps-ledger-closeout.json) — settled P18 surrogate-index construction and P24 cold-start handover to VERIFIED (the fixed "first review" handover checkpoint is refuted); left P14 drift triggers, P19 ask-budget dose, and SP6 portfolio signals BET with materially better-specified designs. Decision spec: docs/superpowers/specs/2026-07-24-r10-gaps-ledger-closeout-design.md.
