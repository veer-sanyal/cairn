# Principles for Resilient Personal Agentic Systems

Research-derived design principles. Every principle carries an evidence grade:

- **[VERIFIED]** — survived 3-vote adversarial verification against primary sources; multi-source or first-party primary documentation.
- **[PREPRINT]** — survived verification but rests on 2025–2026 preprints / benchmark-only results; treat as an informed bet.
- **[BET]** — no surviving evidence either way; a reasoned design decision, labeled as such.
- **[REFUTED]** — claims that FAILED verification and must not be cited or built on.

Every principle carries an annotation line: `Perishability: durable|semi-durable|perishable · Verified: YYYY-MM · Round: R<n>` — durable refreshes on contradiction only, semi-durable within ~2 releases, perishable is probe-not-recall (short windows). The governor's expiry sweep (SP3) reads these fields.

Sources are listed per principle. Rounds: R1 = context/memory (103 agents, 19/25 claims confirmed), R2 = enforcement/self-improvement (103 agents, 16/25 confirmed), R3 = telemetry/abandonment + elicitation/prior art (pending); R5–R9 (failure/capability, verification/epistemics, objective design, human-agent boundary, orchestration/tiering) are pending synthesis — full provenance lands in a later task.

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
Source: Anthropic hooks docs (fetched live Jul 2026). Caveat: open GitHub issues (#37210, #24327) show hook deny enforcement has had real bugs → belt-and-suspenders post-hoc validation for must-never-violate invariants.

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

**[BET — no surviving evidence]** Preference/goal DRIFT detection after setup. No claims survived. Design bet: re-elicit at reviews using the same artifact-based method, triggered by behavioral signals (declining input metrics, typed lapses), not calendar alone.

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

**[BET]** Leading/lagging-indicator design is the weakest-covered sub-area: only Amplitude's leading-indicator requirement and one vendor formalism (Statsig surrogate metrics, Var(X) = Var(S) + MSE — low confidence, single vendor blog) survived. Treat proxy-chain construction as a design bet pending better evidence.

**[REFUTED — do not build on]** The two canonical-sounding leading-indicator methods both died: "behavior-measuring proxies beat stated-intent proxies (NPS as referral stand-in)" (1-2) and "build a leading-indicator chain by backward-chaining from a lagging outcome, each step demonstrably predictive of the next" (0-3). Also: "every success metric must be paired with a counter-metric" as a universal rule (1-2 — continuous guardrail monitoring itself is verified and already in P12); Wells Fargo cross-sell-metric specifics ("~3.5M accounts, sole metric, no guardrails", 0-3) — cite the verified $3B/concealment version above.

**Design implications:**
- The governor runs a scheduled proxy-revalidation sweep (SP3): every proxy-goal link in the metric contract is a dated, testable claim re-checked over time — extremal Goodhart decouples proxies precisely where optimization pushes.
- The builder's metric-contract interview cites mechanisms, not folklore: each input lever gets a causal-validity check, each metric an extreme-range question, and audits look for concealment, not just drift.
- Extends P12: watched-not-chased is not taste — it is the structural mitigation for Goodhart under agentic optimization power, and it needs the revalidation lifecycle above because no static contract stays safe.

---

## Research provenance

4 deep-research rounds, ~415 subagents, ~20.6M subagent tokens, July 19 2026.
R1 context/memory (19/25 claims confirmed) · R2 enforcement/self-improvement (16/25) · R3 telemetry/metrics/abandonment (11 findings) · R4 elicitation/prior art (7 findings).
Raw outputs: research-round{1..4}-*.json alongside this file. 21+ claims refuted across rounds are listed inline — they are load-bearing negatives; do not resurrect them.
