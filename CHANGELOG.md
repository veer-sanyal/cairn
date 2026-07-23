# Changelog

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
