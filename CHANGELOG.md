# Changelog

## 0.7.0 — SYSTEM-MAP.md: the system's flows as a source of truth

- **`docs/SYSTEM-MAP.md`** in every instance — one Mermaid flowchart per workflow with a machine-checkable metadata line (Trigger · Writes · Verification · Boundary) and stable flow ids telemetry can cite (`flow=<id>`). Kernel flows ship pre-authored from a template; the builder appends instance-specific flows before the first commit.
- **Governor maintains it** — an applied BUILD that changes a flow updates the map in the same step; the validator flags staleness (`system_map`, silent when absent — legacy instances get a one-time proposal, never a nag).
- **Audit uses it** — map-first rule: reuse and drift-check an existing SYSTEM-MAP.md (drift is a finding), or reconstruct it as the audit's first deliverable so the doctrine walk cites flow ids.

## 0.6.0 — /cairn:audit (SP4 — the level-zero umbrella is complete)

- **`/cairn:audit`** — point Cairn's diagnosis stack at any existing Claude Code agentic setup: mechanism mapping with measured boot cost (P23/P1), north-star elicitation (P14), environment census + data-access-ladder upgrades (P23), and a doctrine walk (memory, verification, orchestration, Goodhart, boundary, staleness) where every finding carries a principle ref AND file:line evidence. Output: blast-ordered BUILD/PARK/REJECT proposals; dispositions are fix-in-place (git checkpoint first, never destructive), a persistent `AUDIT.md` with anti-re-litigation, or migration to a full instance via a pre-filled /cairn:build hand-off.
- Detects Cairn instances and redirects to `/cairn:review` — the governor outranks the audit where telemetry exists.
- **Traceability audit + gap closure** — a P1–P24 commitments audit (all ~60 traced) surfaced and closed four silent wiring gaps (P16 checkpoint-after-error, P18 builder Goodhart interview, P20 orchestration selector, P22 unconditional annual ceiling) and restored two dropped R5/R8 findings to doctrine (over-constraint + transparency-futility; HORIZON convergence).

Umbrella complete: SP1 research engine (0.3.0) · SP2 doctrine P1–P24 (0.4.0) · SP3 wiring (0.5.0) · SP4 audit (0.6.0).

## 0.5.0 — builder/governor wiring (SP3 of the level-zero umbrella)

- **Environment census + data-access ladder** — the builder enumerates this machine's MCP servers/surfaces and records a rung (1 API → 5 manual) with provenance per data need; the governor re-censuses at review and proposes rung upgrades when the environment improves.
- **pass^k capability probes** — every "the model can do X reliably" assumption is probed (k=5 repeated trials) before scaffolding commits to it; results are dated decisions[] entries the governor can re-probe.
- **Doctrine sweeps in the validator** — `research_expired` (RESEARCH.md Refresh-by dates), `census_stale` (>180d), `proxy_revalidation_due` (annual Goodhart re-check of every lever→north-star link, P18/P22). Deterministic detection, human-gated disposition.
- **Failure-mode telemetry + de-automation** — `/log` friction events carry `failure_mode=` tags (spec/verify/context/overreach/tooling/upkeep, P16); same task class + same tag ≥3 since last review → the governor proposes de-automation or a checked verifier.
- **Boundary contract** — instances carry an autonomy table (act/ask/never, graded by irreversibility) and an ask-budget (default 1/session); v1 enforcement is instructional + telemetry-audited, recorded as a BET.

Umbrella: SP1 (0.3.0) research engine · SP2 (0.4.0) doctrine · SP3 (this) wiring · SP4 (/cairn:audit) next.

## 0.4.0 — level-zero doctrine (SP2 of the level-zero umbrella)

- **PRINCIPLES.md v2** — nine new principles from research rounds R5–R9 (~860 verification agents, 3-vote adversarial): P16 failure taxonomy, P17 capability frontier & probing, P18 Goodhart-resistant objectives, P19 human-agent boundary (ask-budgets, blast radius), P20 orchestration & model tiering, P21 verification & eval design, P22 epistemics & knowledge decay, P23 mechanism selection, P24 cold start [BET].
- **Perishability annotations** — every principle (P1–P24) now carries `Perishability · Verified · Round`; durable refreshes on contradiction, semi-durable within ~2 releases, perishable is probe-not-recall. This is the structural expiry metadata the governor's SP3 sweep will read.
- **Curated [REFUTED] ledger** — folk claims that failed 3-vote verification (fixed sub-mode percentages, heterogeneous-swarm superiority, unscoped CoT-judging gains, ...) are carried as do-not-build-on entries.

Doctrine only — no behavior changes. SP3 (builder/governor wiring) follows.

## 0.3.0 — vendored research engine (SP1 of the level-zero umbrella)

- **`/cairn:research`** — the engine front door: frame the decision, write a GROUNDING block, launch, persist. Builder Stage 2.5 and governor research proposals now route through it; no dependency on any globally-installed research skill.
- **Vendored deep-research workflow** — ships as a skill supporting file (plugins can't ship saved workflows) launched via `scriptPath`; the scaffolder installs a copy into each instance's `.claude/workflows/` so instances get `/deep-research` natively; `/cairn:upgrade` keeps it current.
- **`doctrine_write.py`** — deterministic engine-result → `docs/RESEARCH.md` persister: instance grades (VERIFIED/THIN), refuted negatives, caveats, date stamp, and a perishability class (durable / semi-durable / perishable) that sets a Refresh-by date for future governor sweeps.
- **Degraded mode** — no Workflow tool (non-Pro plan, disabled, denied) → subagent fallback at reduced scale with grades capped at THIN.

Umbrella spec: docs/superpowers/specs/2026-07-23-level-zero-umbrella-design.md (SP2-SP4 follow).

## 0.2.0 — decision lifecycle, blast-ordered asks, bounded auto-adopt lane

- **Decision lifecycle** — `manifest.json` `decisions[]` ids are now immutable stable keys: changing a decision appends a new entry with `supersedes` and annotates the old one (`status: superseded`, `superseded_by`, `superseded_on`) — never renumbered, reused, or rewritten in place. Keeps every proposal cite and RESEARCH.md reference valid forever.
- **Blast + door tags with ask-order** — decisions and governor proposals carry `blast: low|med|high` and `one_way`/`door` tags; the builder interview and the governor both ask/present largest-blast-first, dependencies before size, one-way doors first among equals.
- **Anti-re-litigation** — a REJECTed proposal only re-surfaces citing telemetry events newer than the rejection; the reject event is the memory.
- **Four-clause research bar** (builder Stage 2.5) — research runs only when: load-bearing claim contested/unknown ∧ generalizable evidence plausibly exists ∧ blast ≥ med or one-way ∧ narrow enough for one run. Personal magic numbers stay measure-in-telemetry (BET + tune at review).
- **Advise, don't menu** — every governor proposal carries 2-3 options and a recommended default with its grade, pre-chewed to yes/adjust.
- **Fresh-context second opinion** — scoped to the two moments cairn decisions are expensive: the metric contract before scaffolding (one subagent call per build), and high-blast / one-way / contract-touching / override calls at review. Flag → warn once before recording; proceed-over-flag records `dissent` on the decisions[] entry. Low-blast two-way calls are judged inline, no ceremony.
- **Bounded auto-adopt lane** (opt-in at build, `manifest.auto_adopt.armed`) — the governor auto-applies a proposal only when low-blast ∧ two-way ∧ VERIFIED-backed ∧ outside the metric contract/privacy/caps/money. Every adoption logs `revert_until` (+7d); the boot banner names each in-window adoption every session until closed or reverted; one misgrade revert (or two merits reverts in the last 10) self-suspends the lane until the user re-arms.

Provenance: mechanisms adapted from the stick-dev advisor's decision engine (immutable-ID lifecycle, blast-first ask-order, challenge bar, standing-authorization tier).

## 0.1.0 — initial kernel, builder, governor, upgrade

- **Kernel runtime** — instance-local `python3` hooks: SessionStart boot banner (validator + telemetry gap look-back + trigger rules), SessionEnd session record, PreToolUse Write/Edit and Bash invariant guards. All fail-soft (exit 0; deliberate blocks are JSON `permissionDecision: deny`).
- **Validator** — the "lint": size caps, HOT.md staleness stamp, JSONL integrity, stale review sentinel; `--json` output reused by `/cairn:review`.
- **Telemetry** — local append-only `events.jsonl` via `cairn_lib` + `cairn_event.py`; typed `session`/`lapse`/`intent`/`outcome`/`metric`/`proposal` events, no network.
- **Instance templates** — thin-router `CLAUDE.md`, `HOT.md`, hook-wired `settings.json`, and instance-local `/log` `/suspend` `/conclude` commands.
- **Scaffolder** (`skills/build/scaffold.py`) — deterministic build-config → complete instance generator.
- **Builder** (`/cairn:build`) — artifact-driven interview: user-authored goals, metric contract, if-then compilation onto the closed trigger menu.
- **Governor** (`/cairn:review`) — validator re-pass, memory-lane consolidation (SKIP/MERGE/INSERT), telemetry-cited BUILD/PARK/REJECT proposals with the user as gate.
- **Upgrade** (`/cairn:upgrade` + `merge.py`) — version migration with changelog diff and no-silent-data-loss managed-file merge.
- **Evidence base** — `docs/PRINCIPLES.md`, design spec, and raw verified research shipped with the plugin.

Known v1 deferrals: recall-count demotion (recency-only shipped, [BET]); `/cairn:contribute` upstream learning (opt-in issue template instead); Windows (declared unsupported).
