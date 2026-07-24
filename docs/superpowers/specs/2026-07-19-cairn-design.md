# Cairn — Design Spec

**Date:** 2026-07-19
**Status:** Approved design, pre-implementation
**Evidence base:** [docs/PRINCIPLES.md](../../PRINCIPLES.md) — 15 research-derived principles (P1–P15), each graded VERIFIED / PREPRINT / BET / REFUTED. Raw verified research: [docs/research/](../../research/). Every design decision below cites the principle(s) that justify it; decisions with no evidence either way are marked **[BET]**.

## What Cairn is

A Claude Code plugin that scaffolds resilient, long-lived, personalized agentic systems ("instances") — a PM tracker, a trading advisor, a study coach, any personal domain. It has three layers:

1. **Kernel** — the shared runtime every instance gets: file-memory tiers, boot ritual, hook-enforced invariants, local telemetry.
2. **Builder** (`/cairn:build`) — an artifact-driven interview that produces a personalized instance with a metric contract.
3. **Governor** (`/cairn:review`) — a telemetry-cited, human-gated review and self-improvement loop.

An instance is an ordinary directory + git repo that works with plain Claude Code. Cairn is a dependency, not a cage: the scaffolder copies hooks and commands *into the instance's own `.claude/`* (instance-local, refreshed by `/cairn:upgrade`), so an instance keeps its full runtime discipline even if the plugin is uninstalled — only the builder/governor/upgrade commands live in the plugin itself.

Prior-art position (P15): every individual capability exists scattered in the ecosystem (mobile-spine's interview, CCUsage's local telemetry, Bouncer's independent-model gate); no tool combines them. The integration is the product.

## Non-goals

- No network telemetry, ever. Local JSONL only (P15: CCUsage's 11.5k stars validate local-only demand; P11 supplies the metadata-vs-content split, not locality).
- No streak mechanics or gamification (P13: habit automaticity median 66 days, range 18–254; fixed streaks are ungrounded and guilt loops drive abandonment among exactly the behavior-change users Cairn targets).
- No autonomous kernel self-modification (P10). The kernel ships as versioned releases.
- Not a coding-workflow framework (that's SuperClaude/Agent OS territory). Cairn scaffolds *personal domain systems*.

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
- **Three memory tiers (P5):** HOT.md (hot), working/ (warm, on demand), archive.jsonl (cold, append-only). Demotion is scoring-driven at review time, never deletion. **[BET]** exact demotion scoring (HMO's decay formula is preprint-grade); v1 ships recency-only (nothing records recall counts yet; a Read-matching PostToolUse counter is the named upgrade path), marked in manifest.
- **Write-through (P2):** facts are written to owner files during work and committed; conversation history and compaction summaries are never the durable record (compaction loses specifics 0/3 in recall probes).
- **Sub-agent fan-out (P3):** archive reads and any noisy exploration run in spawned agents with a condensed-return norm; scaffolded commands encode this.
- **Refuted-claims guard (P4, P5):** files are the *durable* tier, not the sole task state ("filesystem as sole authority" was refuted); tiering is for context budget + staleness, not claimed retrieval-accuracy gains.

### 1.2 Boot ritual

SessionStart hook runs the **validator script** (the "lint" referenced throughout: one tested script checking file-size caps, staleness stamps, archive integrity; reused post-hoc by `/cairn:review`) and emits a reconcile banner: HOT.md staleness stamp, git state, telemetry gap (a *look-back* — did the previous session log any non-session events?), validator status. Reconcile-against-reality before work (convergent with P2/P5; also the "welcome back" surface — see 3.3).

**Honesty about the surface:** SessionStart output is context injected for the model (plus `systemMessage` for user-visible text where the platform supports it), not a guaranteed user-facing display — banner *relay* is best-effort by the spec's own P8 standard. The raw validator/gap data therefore always lands in `telemetry/events.jsonl` where the user (and `/cairn:review`) can read it deterministically.

### 1.3 Enforced invariants (hooks, not prose — P8, P9)

Prose instructions measurably decay with turns (direction robust across 15 models; the headline ~39% magnitude is setting-dependent per P8's caveat; ~29% recovery after a wrong turn); PreToolUse hooks hard-block and survive even bypassPermissions. Kernel ships:

| Invariant | Hook | Action |
|---|---|---|
| File-size caps (CLAUDE.md, HOT.md, working files) | PreToolUse on Write/Edit | block over hard cap, warn over soft cap |
| archive.jsonl is append-only | PreToolUse on Write/Edit | block edits/overwrites (appends go through the scaffolded append command) |
| Protected-path Bash ops | PreToolUse on Bash | pattern-block redirects/truncation/`rm` targeting archive.jsonl and working/ — **explicitly heuristic**; Bash is the likelier bypass than out-of-band editors, and review re-validation is the real backstop |
| Telemetry write-through | SessionStart (look-back) | if the *previous* session logged no non-session events, log a gap/lapse event and surface it in the banner |
| Staleness stamp present/fresh | SessionStart | banner warning |
| working/ destructive ops are pipeline-only (see 3.2) | PreToolUse | `Edit` (targeted fact write-through) always allowed — P2 requires it; block `Write`-overwrite of an existing working/ file and file deletion **unless the review sentinel is present** — hooks cannot see which command is active, so `/cairn:review` writes `.cairn/review-in-progress` (with timestamp TTL + cleanup on completion) and the hook checks for it |

Session-end records are written by the **SessionEnd** hook (which can write files but not feed context) — the Stop hook fires after *every* response turn, not at session end, and is not used for any of this.

Hook runtime & fail-soft discipline: POSIX shell (+ python3 where jq-free parsing isn't enough); macOS/Linux for v1, Windows explicitly unsupported (declared in README, not silent). Deliberate blocks exit 2; every other failure path exits 0 with a warning line — a missing interpreter or crashed script must never brick a session. Belt-and-suspenders: `/cairn:review` re-validates all invariants post-hoc, for three reasons — hook enforcement has had real field bugs (open Claude Code issues, P9 caveat), the Bash matcher is heuristic, and hooks only fire inside Claude Code (out-of-band edits bypass them entirely).

Threshold values for caps are **[BET]** — no literature gives numbers; defaults chosen small (CLAUDE.md soft 4KB/hard 8KB; HOT.md soft 6KB/hard 12KB) and recorded in manifest as tunable.

### 1.4 Telemetry schema (P11, P13)

`events.jsonl`, one typed event per line. Vocabulary: OTel GenAI attribute names where they exist (`gen_ai.tool.name`, …; semconv version pinned in manifest — attributes are Development-status), ad-hoc names only for what the spec lacks.

**Every event type has a named writer** — telemetry capture cannot rest on prose discipline (P8), so deterministic writers carry the load and best-effort types are labeled as such:

| Event | Writer | Reliability |
|---|---|---|
| `session` — start/end, duration, boot context cost | SessionStart + **SessionEnd** hooks (Stop fires every turn and is not used) | deterministic |
| `lapse` — **typed: forgot / upkeep / skipped / suspended** (P13) | SessionStart hook on gap detection; cause confirmed conversationally, recoverable by design | deterministic detection, best-effort typing |
| `intent` — what the user came to do (enum per instance) | scaffolded `/log` command; next-boot banner reminder as the fallback nudge | best-effort |
| `outcome` — done / partial / friction (with reason) | same as intent | best-effort |
| `metric` — north-star / input / guardrail observation | scaffolded commands at the moment the lever is pulled; `/cairn:review` backfills | mixed |
| `proposal` — governor lifecycle: proposed / validated / applied / discarded | `/cairn:review` itself | deterministic |

The telemetry-gap check runs at the **next SessionStart** as a look-back counting non-session events from the previous session — hook-written `session` events don't satisfy it.

Token/cost mechanics: hooks do not expose token counts. Boot context cost is estimated by the SessionStart hook from resident-file bytes (~bytes/4); per-session usage, where wanted, is parsed post-hoc from Claude Code's own transcript JSONL (the CCUsage-proven mechanism, P15). Cost derived from token counts (no OTel cost attribute exists — refuted claim). Metadata-only by default; prompt/content capture is per-instance opt-in (P11). Format is plain typed JSONL: borrow the handful of OTel GenAI names that genuinely fit (`gen_ai.usage.*`, `gen_ai.tool.name`); no semconv version-pin ceremony — nearly every Cairn event is domain-specific and no OTel consumer will read this file.

## Component 2: Builder (`/cairn:build`)

Six stages, evidence-shaped (P14). Stage 2.5 — **unprompted domain research** — grounds the
instance's parameters in domain evidence the way the kernel is grounded in agent-systems
evidence: the builder identifies which of its design decisions are empirical questions
(spacing parameters for a study coach, WIP limits for a project tracker), frames each as a
decision-serving research question (directing-research discipline: frame before gathering,
skip settled knowledge, scale effort to stakes), announces the plan (user may trim/skip;
skipped items are graded BET), executes via the strongest available engine (a deep-research
skill/workflow when the environment has one; otherwise a built-in fallback — multi-angle
search subagents, primary sources, one adversarial verifier per load-bearing claim prompted
to refute), and persists graded findings (VERIFIED / THIN / BET, plus refuted negatives) to
the instance's `docs/RESEARCH.md` with a date stamp. Parameters cite findings in manifest
decisions[]; a refuted or unverified claim never becomes a parameter. The governor may
propose re-research when friction traces to a BET/THIN decision or the research is stale.

The stages:

1. **Domain + draft first.** Two or three orienting questions, then immediately generate a **draft scaffold sketch** (proposed files, commands, cadence) and iterate on it with the user — artifact-based elicitation beats question batteries (prototyping elicits most requirements; unstructured interviews least). Preference questions posed as pairwise choices where possible.
2. **User-authored goals.** The user types the north star and what "working" means **in their own words**. The builder refines and structures; it never authors goals (P14: LLM-authored goals → 46.6% vs 72.8% follow-through). Enforced in the builder prompt: reflect-and-refine only.
3. **Metric contract (P12).** Three layers, recorded in manifest.json:
   - **North star** — leading, value-representing, influenceable but *not directly targetable*; watched, never chased.
   - **Input metrics** — the levers daily use actually moves; what reviews act on.
   - **Guardrails** — OEC-style, each measurable-within-period / sensitive / timely. Every instance also gets standing anti-bloat guardrails: boot context cost, ceremony time per session, upkeep burden (P1, P13).
4. **If-then compilation (P14).** Interactively convert goals into implementation intentions — "when X, the system does Y" (implementation intentions: d=.65 meta-analytic; separately, the MCII subgroup result shows interactive delivery beats written documents, g=.465 vs .277). These are compiled by **selecting and parametrizing from a closed, tested menu of trigger templates** (review triggers, banner rules, command protocols) — never by generating freeform hook scripts, keeping scaffolding deterministic. Intent is forced explicit *early* because premature-interpretation lock-in is the documented failure mechanism (P8).
5. **Scaffold.** Template-driven (deterministic, testable), from the kernel templates + the interview's decisions. manifest.json records every design decision with its principle tag, including bets — so later reviews can re-examine bets against accumulated telemetry.

Builder knowledge of platform capabilities (hooks/skills/MCP) comes from a bundled, refreshable snapshot doc — no live research per run (P1: it's all distractor tokens otherwise).

### 2.1 The v1 trigger-template menu (closed, tested)

The complete parametrizable set stage 4 selects from — an implementer builds exactly these eight, nothing freeform:

| Template | Parameters | Compiles to |
|---|---|---|
| Gap nudge | days-threshold | SessionStart banner rule |
| Metric observation prompt | metric, trigger command | scaffolded command step |
| Guardrail regression flag | metric, direction, window | banner rule + review input |
| Friction accumulator | count-threshold, window | banner "review suggested" rule |
| Review-due reminder | cadence | banner rule |
| Staleness escalation | file, age-threshold | banner rule (validator already checks) |
| Intent enum | the instance's intent labels | `/log` command choices |
| Suspend suggestion | lapse-count threshold | banner rule offering `/suspend` honorably |

Menu growth is a kernel-release matter (P10), not a per-instance one.

> **Amendment (2026-07-24, as of 0.8.1):** the shipped trigger-template menu is the five
> banner-rule templates — `gap_nudge`, `review_due`, `staleness_escalation`,
> `friction_accumulator`, `suspend_suggestion`. Of the original eight above, guardrail
> regression is compiled into `manifest.metrics.guardrails` (a standing banner check, not a
> parametrized trigger), metric-observation prompts are scaffolded command steps, and the
> intent enum is a manifest field rendered into `/log` — manifest/command compilation
> targets, not trigger templates. The table stands as the original design record.

## Component 3: Governor (`/cairn:review`)

### 3.1 Cadence

Default monthly, tunable; never weekly-or-faster for adoption judgments (P13: habit horizon is months). Claude Code has no scheduler, so the **SessionStart banner is the sole trigger surface**: it nudges when a review is due by calendar or when behavioral signals fire — repeated friction events, guardrail regression, typed lapses; never turn counts (all turn-count thresholds were refuted, P8). A review only ever runs when the user invokes `/cairn:review`.

### 3.2 The pipeline (P6, P10)

Intrinsic self-correction degrades performance; the workable pattern is proposal → external validation → gate. One pipeline, two lanes:

- **Memory lane** (per review): probe-verify-repair — synthesize probe questions from recent sessions, test HOT.md + working/ against them, convert failures into repair proposals, consolidate via SKIP / MERGE / INSERT. The SKIP/MERGE/INSERT discipline is **protocol, verified post-hoc by the review's own validator pass** — the 1.3 hook blocks only overwrite/delete (Edit stays open for write-through, so a hook cannot fully enforce consolidation shape). Demotion scoring runs here.
- **System lane** (proposals to change the instance itself): every proposal must **cite telemetry** (metric/friction/lapse events — no vibes features), must not regress the standing anti-bloat guardrails, and lands only through **BUILD / PARK / REJECT with the user as the gate**. Validation is empirical where possible (tests, before/after telemetry deltas); discard-on-failure. Contrast in the wild: SuperClaude's ungated auto-loop (P15).

### 3.3 Abandonment handling (P13)

- Boot banner after a gap: "welcome back + what changed" — never a guilt screen.
- Lapse cause captured as typed event; **upkeep-burden lapses are treated as kernel bugs** (the system demands too much manual writing — automate or delete the demand).
- `/suspend` and `/conclude` (instance-local commands, so they survive plugin uninstall) are first-class: a system whose habit the user has internalized *concludes successfully*, and telemetry can tell that apart from decay.
- Drift **[BET]**: reviews re-run the artifact-based elicitation against the manifest goals when input metrics decline or lapses accumulate; no drift-detection literature survived, so this is a labeled bet.

## Kernel evolution & community

- Kernel changes ship as versioned plugin releases; instances pin a version; `/cairn:upgrade` migrates with a changelog diff. Never silent self-modification (P10).
- **Upgrade merge semantics (no silent data loss inside a user's repo):** three file classes. (1) *Hook scripts* are plugin-owned and never user-edited → direct-copied over on upgrade (each replacement reported) — routing them through a header-based merge was found in build review to make upgrades a silent no-op, since scaffolded hooks carry no header. (2) *Command files* are managed-but-rendered → the new template is rendered with the instance's manifest values and merged: identical → no-op; user-modified → new version lands alongside as `<name>.cairn-new` (latest `.cairn-new` wins), user's file never overwritten. (3) *CLAUDE.md and HOT.md* are user-owned living documents after scaffold → never upgraded; their `managed-by-cairn` header records provenance only.
- Upstream learning: deferred past v1 (YAGNI — no community exists yet); a CONTRIBUTING.md line covers it until real users do. Because no-network telemetry means Cairn's own north star is uncollectable in aggregate (the author only ever sees dogfood instances), the public feedback channel is an **opt-in issue template** asking users to paste their locally-computed stats.

## Repo shape (the published plugin)

```
cairn/
  .claude-plugin/plugin.json + marketplace.json   # self-hosted single-plugin marketplace;
                                                  # install: /plugin marketplace add veer-sanyal/cairn
  skills/build/  skills/review/  skills/upgrade/  # plugin-resident: /cairn:build /cairn:review
                                                  #   /cairn:upgrade (the machinery)
  templates/                                      # instance scaffold (deterministic), INCLUDING
    hooks/                                        #   all runtime hooks — template payload copied
    commands/                                     #   into each instance's .claude/, INCLUDING
                                                  #   suspend/conclude/log — abandonment features
                                                  #   (P13) must survive plugin uninstall, so they
                                                  #   are instance-local, not plugin skills.
                                                  #   The PLUGIN registers NO hooks of its own
                                                  #   (they would fire in every project)
  capabilities/snapshot.md                        # refreshable platform-capability doc
  docs/PRINCIPLES.md  docs/research/              # the evidence base, shipped with the product
  tests/
```

The methodology ships inside the repo — people who want the ideas without the plugin get PRINCIPLES.md. README leads with a concrete before/after example (interview → a study coach that survives three months of real life), then the three differentiators: metric contract, typed-lapse abandonment model, human-gated governor.

## Trust: what Cairn executes on your machine

Destined for the README, near the top — a stranger's first question about a plugin that writes hooks into their directories:

- **What runs:** small POSIX-shell/python3 scripts, all readable in `templates/hooks/` before install and in your instance's `.claude/` after; nothing obfuscated, nothing compiled.
- **When:** only inside instance directories you scaffolded (the plugin registers zero global hooks), at session start/end and before tool calls.
- **Network: never.** No script makes a network call; telemetry is local JSONL you can `cat`.
- **Removal:** uninstall the plugin and instances keep working (runtime is instance-local); delete an instance directory and Cairn retains nothing about it.

## Lifecycle (v1 scope declarations)

- **First session after scaffold:** boot banner shows "new instance" state; `/cairn:review` refuses to run adoption judgments until a minimum telemetry window exists (**[BET]**, ledgered: default 10 sessions or 4 weeks, manifest-tunable — and adoption *verdicts* specifically are deferred to the P13 habit horizon of ~2 months; the earlier window permits only invariant re-validation and memory-lane consolidation).
- **Single machine, single session at a time.** Multi-machine git sync is explicitly out of scope for v1: `events.jsonl`/`archive.jsonl` appends would union-merge, but `HOT.md` rewrites would not. Documented limitation, not a silent one.
- **Offboarding:** `/cairn:conclude` writes a final state summary to the archive and stamps the manifest; the instance directory remains a plain readable git repo forever — no lock-in to delete.

## Validation plan (pre-publish)

1. Build kernel + templates; hook scripts and scaffolder covered by tests.
2. **Dogfood migration:** migrate one existing real system (Veer PM) onto the kernel as test-user #1 — stress-tests the runtime against real accumulated state. Private; never enters the repo.
3. **Greenfield build:** run `/cairn:build` end-to-end for a new domain — stress-tests the interview.
4. Run both for a telemetry-meaningful period; run one real `/cairn:review` cycle.
5. Publish to GitHub (account: veer-sanyal) with the research corpus included.

Cairn's own success measures, computable locally by any user from their own telemetry: north star = instances still in active-or-concluded-successfully state at 3 months (P13 horizon); guardrails = boot context cost and upkeep-burden lapse rate.

## Engineering posture

- Scaffolding deterministic (templates), not freeform generation.
- Hooks fail soft; review re-validates invariants post-hoc.
- Every non-trivial script leaves a runnable check (test or assert-based self-check).
- Ecosystem-facing content (capabilities snapshot, prior-art notes) is dated — July 2026 snapshots rot fast (P15).

## Open bets & preprint-grade decisions ledger (revisit against telemetry)

**[BET] — no evidence either way:**

| Bet | Why it's a bet | Revisit when |
|---|---|---|
| Demotion scoring heuristic | HMO formula is preprint-grade | archive misses show up in probe-repair |
| File-size cap values | no literature gives numbers | caps block legitimate work or never fire |
| Drift re-elicitation trigger | no surviving drift evidence | input metrics decline without lapses |
| Interview length/depth | elicitation studies used students, not solo users | build-session friction events |
| "Unfilled niche" beyond Claude Code ecosystem | Letta/Mem0/Agent OS never verified | before public positioning claims |
| Minimum telemetry window (10 sessions / 4 weeks) | no literature gives a number; sits below P13's 66-day habit median, which is why adoption verdicts wait ~2 months | window blocks useful early reviews, or early verdicts prove wrong |
| Bash-matcher heuristic coverage | no way to enumerate all destructive shell patterns | review re-validation catches bypasses in practice |

**[PREPRINT] — evidence-backed but not settled science; load-bearing decisions that must not read as VERIFIED:**

| Decision | Evidence status | Revisit when |
|---|---|---|
| SKIP/MERGE/INSERT consolidation pipeline (hook-enforced, 3.2) | P6: MemMA, benchmark-only, one claim survived 2-1 | probe-repair pass produces bad merges or peer review lands |
| Builder never authors goals (2, stage 2) | P14: single preregistered preprint (46.6% vs 72.8%); mediation mechanism refuted | replication appears, or build-session friction shows refine-only is too rigid |
