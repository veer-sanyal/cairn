# Keel — Design Spec

**Date:** 2026-07-19
**Status:** Approved design, pre-implementation
**Evidence base:** [docs/PRINCIPLES.md](../../PRINCIPLES.md) — 15 research-derived principles (P1–P15), each graded VERIFIED / PREPRINT / BET / REFUTED. Raw verified research: [docs/research/](../../research/). Every design decision below cites the principle(s) that justify it; decisions with no evidence either way are marked **[BET]**.

## What Keel is

A Claude Code plugin that scaffolds resilient, long-lived, personalized agentic systems ("instances") — a PM tracker, a trading advisor, a study coach, any personal domain. It has three layers:

1. **Kernel** — the shared runtime every instance gets: file-memory tiers, boot ritual, hook-enforced invariants, local telemetry.
2. **Builder** (`/keel:build`) — an artifact-driven interview that produces a personalized instance with a metric contract.
3. **Governor** (`/keel:review`) — a telemetry-cited, human-gated review and self-improvement loop.

An instance is an ordinary directory + git repo that works with plain Claude Code. Keel is a dependency, not a cage: the scaffolder copies hooks and commands *into the instance's own `.claude/`* (instance-local, refreshed by `/keel:upgrade`), so an instance keeps its full runtime discipline even if the plugin is uninstalled — only the builder/governor/upgrade commands live in the plugin itself.

Prior-art position (P15): every individual capability exists scattered in the ecosystem (mobile-spine's interview, CCUsage's local telemetry, Bouncer's independent-model gate); no tool combines them. The integration is the product.

## Non-goals

- No network telemetry, ever. Local JSONL only (P11 privacy precedent; CCUsage's 11.5k stars validate local-only demand).
- No streak mechanics or gamification (P13: habit automaticity median 66 days, range 18–254; fixed streaks are ungrounded and guilt loops drive abandonment among exactly the behavior-change users Keel targets).
- No autonomous kernel self-modification (P10). The kernel ships as versioned releases.
- Not a coding-workflow framework (that's SuperClaude/Agent OS territory). Keel scaffolds *personal domain systems*.

## Component 1: Kernel

### 1.1 Instance file anatomy

```
<instance>/
  CLAUDE.md            # thin router: identity, ownership map, pointers. Hard cap (lint) — P1
  manifest.json        # metric contract + every design decision + kernel version pin
  state/
    HOT.md             # lean current-state snapshot; boots every session; staleness stamp — P5
    working/           # mid-tier owner files, loaded on demand via CLAUDE.md pointers — P4,P5
    archive.jsonl      # append-only history; subagent-only access — P3,P5
  telemetry/
    events.jsonl       # local-only, OTel GenAI vocabulary — P11
  .claude/
    commands/          # instance protocols, loaded on demand — P1,P4
    hooks/  settings.json
```

- **Index-first (P1, P4):** CLAUDE.md holds pointers and an ownership map (one fact = one owner file), never content. Content loads just-in-time. Naming/size/timestamp conventions are part of the agent-facing API.
- **Three memory tiers (P5):** HOT.md (hot), working/ (warm, on demand), archive.jsonl (cold, append-only). Demotion is scoring-driven at review time, never deletion. **[BET]** exact demotion scoring (HMO's decay formula is preprint-grade); v1 uses recency + recall-count heuristics, marked in manifest.
- **Write-through (P2):** facts are written to owner files during work and committed; conversation history and compaction summaries are never the durable record (compaction loses specifics 0/3 in recall probes).
- **Sub-agent fan-out (P3):** archive reads and any noisy exploration run in spawned agents with a condensed-return norm; scaffolded commands encode this.
- **Refuted-claims guard (P4, P5):** files are the *durable* tier, not the sole task state ("filesystem as sole authority" was refuted); tiering is for context budget + staleness, not claimed retrieval-accuracy gains.

### 1.2 Boot ritual

SessionStart hook prints a reconcile banner: HOT.md staleness stamp, git state, telemetry gap (sessions since last event), lint status. Reconcile-against-reality before work (convergent with P2/P5; also the "welcome back" surface — see 3.3).

### 1.3 Enforced invariants (hooks, not prose — P8, P9)

Prose instructions measurably decay with turns (~39% drop; ~29% recovery); PreToolUse hooks hard-block and survive even bypassPermissions. Kernel ships:

| Invariant | Hook | Action |
|---|---|---|
| File-size caps (CLAUDE.md, HOT.md, working files) | PreToolUse on Write/Edit | block over hard cap, warn over soft cap |
| archive.jsonl is append-only | PreToolUse | block edits/overwrites |
| Telemetry write-through | Stop hook | warn if session ends with no event logged |
| Staleness stamp present/fresh | SessionStart | banner warning |
| Memory consolidation is pipeline-only (see 3.2) | PreToolUse | block direct rewrites of working/ outside /keel:review |

Hook scripts are small, tested, and fail soft (a broken hook warns; it never bricks a session). Belt-and-suspenders: because hook enforcement has had real field bugs (open Claude Code issues), `/keel:review` re-validates all invariants post-hoc (P9 caveat).

Threshold values for caps are **[BET]** — no literature gives numbers; defaults chosen small (CLAUDE.md soft 4KB/hard 8KB; HOT.md soft 6KB/hard 12KB) and recorded in manifest as tunable.

### 1.4 Telemetry schema (P11, P13)

`events.jsonl`, one typed event per line. Vocabulary: OTel GenAI attribute names where they exist (`gen_ai.usage.input_tokens`, `gen_ai.tool.name`, …; semconv version pinned in manifest — attributes are Development-status), ad-hoc names only for what the spec lacks:

- `session` — start/end, duration, boot context cost (tokens resident at boot)
- `intent` — what the user came to do (enum per instance, defined at build)
- `outcome` — done / partial / friction (friction carries a reason)
- `metric` — a north-star / input / guardrail observation (see 2.2)
- `lapse` — **typed: forgot / upkeep / skipped / suspended** (P13); written by the boot banner on gap detection, cause confirmed conversationally, recoverable by design
- `proposal` — governor lifecycle: proposed / validated / applied / discarded (see 3.2)

Metadata-only by default; prompt/content capture is per-instance opt-in (P11). Cost derived from token counts (no OTel cost attribute exists — refuted claim).

## Component 2: Builder (`/keel:build`)

Five stages, evidence-shaped (P14):

1. **Domain + draft first.** Two or three orienting questions, then immediately generate a **draft scaffold sketch** (proposed files, commands, cadence) and iterate on it with the user — artifact-based elicitation beats question batteries (prototyping elicits most requirements; unstructured interviews least). Preference questions posed as pairwise choices where possible.
2. **User-authored goals.** The user types the north star and what "working" means **in their own words**. The builder refines and structures; it never authors goals (P14: LLM-authored goals → 46.6% vs 72.8% follow-through). Enforced in the builder prompt: reflect-and-refine only.
3. **Metric contract (P12).** Three layers, recorded in manifest.json:
   - **North star** — leading, value-representing, influenceable but *not directly targetable*; watched, never chased.
   - **Input metrics** — the levers daily use actually moves; what reviews act on.
   - **Guardrails** — OEC-style, each measurable-within-period / sensitive / timely. Every instance also gets standing anti-bloat guardrails: boot context cost, ceremony time per session, upkeep burden (P1, P13).
4. **If-then compilation (P14).** Interactively convert goals into implementation intentions — "when X, the system does Y" (d=.65; interactive delivery beats documents). These become the instance's hooks, review triggers, and command protocols. Intent is forced explicit *early* because premature-interpretation lock-in is the documented failure mechanism (P8).
5. **Scaffold.** Template-driven (deterministic, testable), from the kernel templates + the interview's decisions. manifest.json records every design decision with its principle tag, including bets — so later reviews can re-examine bets against accumulated telemetry.

Builder knowledge of platform capabilities (hooks/skills/MCP) comes from a bundled, refreshable snapshot doc — no live research per run (P1: it's all distractor tokens otherwise).

## Component 3: Governor (`/keel:review`)

### 3.1 Cadence

Default monthly, tunable; never weekly-or-faster for adoption judgments (P13: habit horizon is months). Also triggerable by behavioral signals — repeated friction events, guardrail regression, typed lapses — never by turn counts (all turn-count thresholds were refuted, P8).

### 3.2 The pipeline (P6, P10)

Intrinsic self-correction degrades performance; the workable pattern is proposal → external validation → gate. One pipeline, two lanes:

- **Memory lane** (per review): probe-verify-repair — synthesize probe questions from recent sessions, test HOT.md + working/ against them, convert failures into repair proposals, consolidate via SKIP / MERGE / INSERT (never freeform rewriting — the hook from 1.3 enforces this). Demotion scoring runs here.
- **System lane** (proposals to change the instance itself): every proposal must **cite telemetry** (metric/friction/lapse events — no vibes features), must not regress the standing anti-bloat guardrails, and lands only through **BUILD / PARK / REJECT with the user as the gate**. Validation is empirical where possible (tests, before/after telemetry deltas); discard-on-failure. Contrast in the wild: SuperClaude's ungated auto-loop (P15).

### 3.3 Abandonment handling (P13)

- Boot banner after a gap: "welcome back + what changed" — never a guilt screen.
- Lapse cause captured as typed event; **upkeep-burden lapses are treated as kernel bugs** (the system demands too much manual writing — automate or delete the demand).
- `/keel:suspend` and `/keel:conclude` are first-class: a system whose habit the user has internalized *concludes successfully*, and telemetry can tell that apart from decay.
- Drift **[BET]**: reviews re-run the artifact-based elicitation against the manifest goals when input metrics decline or lapses accumulate; no drift-detection literature survived, so this is a labeled bet.

## Kernel evolution & community

- Kernel changes ship as versioned plugin releases; instances pin a version; `/keel:upgrade` migrates with a changelog diff. Never silent self-modification (P10).
- `/keel:contribute` drafts an anonymized GitHub issue from a locally-learned pattern; the user reviews and posts it themselves. Learning flows upstream without data leaving the machine.

## Repo shape (the published plugin)

```
keel/
  .claude-plugin/plugin.json + marketplace.json
  skills/build/  skills/review/          # builder + governor
  hooks/                                  # tested shell/python, fail-soft
  templates/                              # instance scaffold (deterministic)
  capabilities/snapshot.md                # refreshable platform-capability doc
  docs/PRINCIPLES.md  docs/research/      # the evidence base, shipped with the product
  tests/
```

The methodology ships inside the repo — people who want the ideas without the plugin get PRINCIPLES.md.

## Validation plan (pre-publish)

1. Build kernel + templates; hook scripts and scaffolder covered by tests.
2. **Dogfood migration:** migrate one existing real system (Veer PM) onto the kernel as test-user #1 — stress-tests the runtime against real accumulated state. Private; never enters the repo.
3. **Greenfield build:** run `/keel:build` end-to-end for a new domain — stress-tests the interview.
4. Run both for a telemetry-meaningful period; run one real `/keel:review` cycle.
5. Publish to GitHub (account: veer-sanyal) with the research corpus included.

Keel's own success measures, computable locally by any user from their own telemetry: north star = instances still in active-or-concluded-successfully state at 3 months (P13 horizon); guardrails = boot context cost and upkeep-burden lapse rate.

## Engineering posture

- Scaffolding deterministic (templates), not freeform generation.
- Hooks fail soft; review re-validates invariants post-hoc.
- Every non-trivial script leaves a runnable check (test or assert-based self-check).
- Ecosystem-facing content (capabilities snapshot, prior-art notes) is dated — July 2026 snapshots rot fast (P15).

## Open bets ledger (revisit against telemetry)

| Bet | Why it's a bet | Revisit when |
|---|---|---|
| Demotion scoring heuristic | HMO formula is preprint-grade | archive misses show up in probe-repair |
| File-size cap values | no literature gives numbers | caps block legitimate work or never fire |
| Drift re-elicitation trigger | no surviving drift evidence | input metrics decline without lapses |
| Interview length/depth | elicitation studies used students, not solo users | build-session friction events |
| "Unfilled niche" beyond Claude Code ecosystem | Letta/Mem0/Agent OS never verified | before public positioning claims |
