# Cairn

> A cairn is a hand-stacked trail marker. It survives the seasons, asks nothing of you,
> and when you come back — after a week, after a month — it shows you exactly where you
> left off. That's what this plugin builds.

<p align="center">
  <img src="assets/cairn.svg" alt="A cairn — a balanced stack of trail-marker stones" width="150" />
</p>

Cairn is a [Claude Code](https://claude.com/claude-code) plugin that interviews you and
scaffolds a **long-lived agentic system** — one that remembers across months, stays honest
about what it knows, and never loses the thread when you step away. It isn't tied to one
domain. Point it at almost any goal that needs memory, discipline, and time, and it designs
a system for that goal — even one it has never seen before.

The way to think about Cairn is as **a systems engineer who works like a product manager and
does their own research.** Hand it a goal and, before it builds anything, it breaks the goal
down the way a good PM would:

- **What's the North Star metric** for this system — the one leading, value-representing
  outcome we watch?
- **What are the input levers** — the metric tree beneath it that daily use actually moves?
- **What are we trying to maximize? To minimize?**
- **What are the guardrail metrics**, and what are their hard limits?

Then it puts on its engineering hat. It understands the fundamental technology of building
agentic systems — how context rot degrades long sessions, how memory has to be tiered and
externalized to survive session boundaries, when to fan out to sub-agents and when parallelism
just burns tokens, where deterministic enforcement beats prose, how objectives corrupt under
optimization — and it designs *within* those constraints. Three things let it do that for a
domain it's never seen:

- a bundled **level-zero doctrine** — 24 evidence-graded principles about how agentic systems
  fail, how objectives corrupt, where the human boundary sits, and when knowledge expires;
- a **vendored research engine** that manufactures the domain-specific knowledge each instance
  needs *at build time* — so it reasons about your domain from verified findings, not bluff;
- an **environment census** of what your machine can actually do — which tools, connectors,
  and models are within reach.

Give it a domain and it designs, probes, and governs a system for it. It can also
[audit an agentic setup you already have](#the-commands) against the same doctrine.

## What you can build with it

Cairn is a kernel, not a category. Anything that benefits from durable memory, an honest
success metric, and a monthly check-in is a candidate:

| You want to… | Cairn scaffolds |
|---|---|
| **Learn something over months** — a language, a curriculum, a certification | A study coach with spaced memory, a mastery metric *you* defined, and reviews that only propose changes your usage data justifies. |
| **Run a job search** | A tracker that remembers every application, thread, and deadline; surfaces "where things stand" on boot; and never nags you with a broken streak after a quiet week. |
| **Train for something physical** | A training log that tracks load and recovery, flags when upkeep is costing you more than it returns, and treats a suspended block as honorable, not failure. |
| **Keep a writing or research practice** | A system with an append-only history of what you've drafted, graded domain findings that refresh on schedule, and a governor that consolidates notes instead of letting them rot. |
| **Manage a long project or investigation** | A workspace with a `SYSTEM-MAP.md` of every workflow, a boundary contract for what the agent may do unasked, and telemetry you can audit line by line. |
| **Harden an agentic setup you already run** | `/cairn:audit` — a diagnosis against the doctrine, with blast-ordered fixes and an optional migration path. |

The common thread: these are systems about a goal you'll come back to for months, where the
enemy is drift, stale knowledge, and abandonment — not a one-off task you'd hand a plain
prompt.

### A worked example: the metric tree it builds

Say you point Cairn at *"get conversational in Spanish before a trip in six months."* The
interview doesn't just make a folder — it reasons about the goal like a PM sizing a product,
and won't scaffold until the tree holds together:

```
North Star   (leading, value-representing, watched — never chased)
└─ Conversational reach: % of a target scenario you can carry unscripted

   Input levers   (the metric tree daily use actually moves — 1 to 3, kept review-actionable)
   ├─ maximize · active vocabulary retained (spaced-recall, not lifetime "seen")
   ├─ maximize · speaking minutes per week (production, not passive input)
   └─ minimize · time-to-recall on known words (fluency, not just correctness)

   Guardrails   (hard limits — a breach is a finding at review)
   ├─ minimize · boot context cost — stays under budget
   ├─ minimize · weekly upkeep burden — stays under ~N minutes
   └─ the North Star is never targeted directly (that's what makes it game-resistant)
```

Notice what it *refuses* to do: it won't let "words seen" masquerade as a North Star (a lagging,
gameable count), it separates the outcome you watch from the levers you pull, and it bakes in
guardrails so the system optimizing itself can't quietly cost you more than it returns. Before it
hardens the contract, it stress-tests each lever — *would moving this actually move the North
Star, or do they just correlate?* (practicing basketball doesn't make you taller) — and asks what
each metric would reward at 10x range. That discipline — north star as a *dependent* variable,
levers as independent ones, guardrails as OEC components, every proxy-to-goal link causally
checked — is the same on a training log, a job search, or a research practice. Only the domain
research underneath it changes.

**Before:** you ask Claude to help you study; three weeks later the folder is a graveyard of
stale notes and you're re-explaining everything from scratch.

**After `/cairn:build`:** a ~15-minute interview scaffolds a coach with its own memory
discipline, a success metric *you wrote in your own words*, and a monthly review that only
proposes changes your usage data justifies — and when you come back after a break it greets
you with *"here's where things stand,"* never a broken streak.

## Install

```
/plugin marketplace add veer-sanyal/cairn
/plugin install cairn
```

Then, in an empty directory:

```
/cairn:build
```

Requires macOS/Linux and python3 (stdlib only — no pip installs). Windows is not supported
in v1.

## How it works

### 1. The build interview

`/cairn:build` doesn't hand you a form. It interviews you by **showing drafts** — proposing a
concrete scaffold sketch early and iterating on it — because artifact-based elicitation
surfaces far more real requirements than open-ended questioning, and because a goal you author
yourself is one you actually follow through on. It won't scaffold until you've declared a
**metric contract** in your own words (see below). Along the way it runs the research engine to
manufacture the domain knowledge your system needs, and takes a census of your machine so it
designs within what you can actually run.

### 2. What lands on disk

Every instance Cairn scaffolds is an ordinary directory + git repo that works with plain
Claude Code — the plugin is a dependency, not a cage:

```
your-instance/
  CLAUDE.md              # thin router: what this system is, where each fact lives
  manifest.json          # metric contract, boundary contract, census, every decision with its grade
  docs/
    SYSTEM-MAP.md        # every flow as a mermaid diagram — the system's source of truth
    RESEARCH.md          # graded domain findings with refresh-by dates, from the research engine
  state/
    HOT.md               # lean "where things stand" snapshot — boots every session
    working/             # topic files, loaded on demand
    archive.jsonl        # append-only history (hook-enforced)
  telemetry/
    events.jsonl         # local-only usage log — cat it any time
  .claude/
    hooks/               # the kernel runtime, copied INTO your instance
    commands/            # /log, /suspend, /conclude — yours even if you uninstall Cairn
    workflows/           # your own copy of the deep-research engine (/deep-research)
```

### 3. `SYSTEM-MAP.md` — the source of truth for what your system *does*

The map holds one flow per section — each a Mermaid flowchart plus a machine-checkable
metadata line: **Trigger · Writes · Verification · Boundary** (`act` | `ask` | `never`).
Kernel flows (session boot, telemetry, write-guards, the review cycle, upgrades) ship
pre-authored; the builder appends one section per workflow it designs for *your* domain before
the first commit.

It isn't documentation that drifts from reality — it's enforced. When a flow changes, the map
changes in the same commit, and the governor flags staleness at review. Flow ids are stable, so
telemetry can cite them (`flow=<id>`) and an audit can drift-check the map against what the code
actually does.

### 4. Every session boots cheap and honest

A `SessionStart` hook reconciles reality before you work: it appends a session event, notices
any gap since last time (typing the lapse — see below), and prints a *"where things stand"*
banner drawn from the lean `HOT.md` snapshot. The router (`CLAUDE.md`) stays thin on purpose;
detail loads from `state/working/` only when a turn needs it. You never re-explain the system.

### 5. The governor keeps it healthy

`/cairn:review` is a governed cycle, not a rewrite: it re-validates the invariants, consolidates
memory through a *probe → verify → repair* pipeline (never freeform rewriting), reports your
metrics, and surfaces changes as **BUILD / PARK / REJECT** proposals. **You are the gate.**
Nothing self-applies, because models reviewing their own work without external feedback
measurably get *worse*.

## The commands

| Command | What it does |
|---|---|
| `/cairn:build` | Interview → metric contract → scaffold. Shows you drafts and iterates; **you** author the goals, it only refines them. |
| `/cairn:research` | The research engine: frames a decision, runs a claim-scaled 3-vote adversarial deep-research workflow, persists graded findings (with refresh-by dates) into the instance's `docs/RESEARCH.md`. Used by build and review; callable directly. |
| `/cairn:audit` | Diagnose an existing (non-Cairn) agentic setup against the doctrine: measured boot cost, missing metric contract, census + ladder upgrades, verification gaps — blast-ordered BUILD/PARK/REJECT fixes, or migrate via a pre-filled `/cairn:build`. |
| `/cairn:review` | The governor: re-validates invariants, consolidates memory (probe → verify → repair), reports your metrics, and proposes changes as **BUILD / PARK / REJECT** — you are the gate. |
| `/cairn:upgrade` | Migrates an instance to a new kernel version. Never overwrites a file you've modified — new versions land alongside as `.cairn-new`. |
| `/cairn:list` | Portfolio view of every instance on this machine — status (active/suspended/concluded), routing by name ("open my job system"), and read-only peeks into another instance's state. |
| `/log` `/suspend` `/conclude` | Instance-local. Log intent/outcome/metrics; pause honorably; or conclude — **concluding is a success state**, not churn. |

## The four ideas

**1. A metric contract, or no instance.**
The interview won't scaffold until you've declared — in your own words — a north star
(watched, never chased), the input levers your daily use actually moves, and guardrail metrics
with hard limits. Reviews act on inputs and guardrails; the north star is the thing they
protect. Every instance also carries standing anti-bloat guardrails (boot context cost, upkeep
burden) that no proposed change may regress.

**2. Lapses are typed, recoverable, and never shamed.**
The abandonment research is unambiguous: people stop tracking for four distinct reasons —
forgetting, upkeep burden, deliberate skipping, suspending — and lapsing is usually temporary.
So Cairn types every lapse instead of flagging churn, treats **upkeep lapses as kernel bugs**
(the system demanded too much writing — that's Cairn's fault, not yours), ships no streaks and
no guilt screens, and makes `/conclude` first-class: a system you outgrew because the habit
stuck is a *win*, and the telemetry can tell that apart from decay.

**3. Self-improvement with a human gate.**
Models reviewing their own work without external feedback measurably get *worse* — so nothing
in Cairn self-applies. Reviews must cite your telemetry events (no vibes features), proposals
arrive as BUILD / PARK / REJECT for you to decide, and the kernel itself only changes through
versioned releases you explicitly upgrade to.

**4. Knowledge is manufactured, graded, and expires on schedule.**
The kernel knows *methods* (level-zero doctrine: failure taxonomy, Goodhart resistance,
orchestration economics, the human-agent boundary); it never pretends to know your domain.
Domain knowledge is produced per instance by a claim-scaled, 3-vote adversarial research engine,
persisted with evidence grades and **perishability classes** — and because models can't feel
their own knowledge going stale (~55%, a coin flip), expiry is structural: refresh-by dates,
census diffs, and an unconditional annual ceiling that the governor sweeps deterministically.

## The doctrine, in brief

Cairn's behavior is downstream of 24 research-derived principles
([**docs/PRINCIPLES.md**](docs/PRINCIPLES.md) has each one graded, sourced, and dated). The
short version, grouped:

**Memory & context**
- Context is a budgeted, degrading resource — anything not needed *this turn* is a distractor that actively hurts. Boot thin.
- Fine-grained facts live in files, never in summarized history; session boundaries are only survivable via files.
- Tiered hot/cold memory (boot snapshot → working store → append-only archive) with scored demotion, never deletion.
- Consolidation is *probe → verify → repair*, not freeform rewriting.

**Enforcement & self-improvement**
- Instruction drift is real and large (~39% avg drop across 15 models) — so invariants are **hooks, not prose that decays with turns**.
- Deterministic gates (Claude Code hooks) are the enforcement primitive; prose discipline is UX, not enforcement.
- No self-modification lands on model self-review alone — every change passes tests, telemetry deltas, or a human gate.

**Metrics & objectives**
- North star as a leading, value-representing dependent variable (watched); input metrics as the levers; guardrails as hard limits.
- Objectives corrupt under optimization in four distinct ways (Goodhart) — each input lever gets a causal-validity check, and proxy-goal links are re-validated on a schedule.

**Abandonment**
- It's the dominant failure mode — typed, often temporary, and not always failure. Upkeep burden is a kernel bug; `/conclude` is a success state.
- Cadence is measured in months, not weeks. No fixed streaks.

**Capability & verification**
- The capability frontier is *probed, never recalled* — "the model can do X" is a dated, re-probed claim (pass^k, not pass@k).
- "A verifier ran" is not evidence — verifiers must record what they checked against the objective. Same for "a human approved it."
- Judges are instruments: rubric-first, calibrated against human labels, reported as probabilities.

**Orchestration**
- Default single-threaded; fan-out is bought with tokens (multi-agent can cost ~15x). Escalate only on measured evidence.
- Side-effectful work is single-writer; spawn readers and advisors freely, never parallel write authority.

**Knowledge & the human boundary**
- Knowledge expires on events, not clocks — and models can't feel it going stale, so expiry is structural (refresh-by dates, an annual ceiling).
- Autonomy is graded by blast radius; asks are a rationed budget. Irreversible + externally-visible actions are never autonomous, and their gate is inhibitive, not a passive confirm.
- A fresh instance runs on inherited doctrine until its own telemetry earns authority at the first review.

## Enforced, not requested

Long-conversation instruction drift is real and large (~39% average performance drop across 15
models in multi-turn studies), which is why Cairn's invariants are **hooks, not prose**:
file-size caps that keep your router lean, an append-only archive, guarded overwrites of memory
files, a session banner that reconciles reality before work. Hooks fail soft — a broken script
warns, it never bricks a session — and every invariant is re-validated post-hoc at review,
because hooks can't see edits made outside Claude Code.

Verified live, not just in tests: the boot banner reaches the model, session telemetry writes
with real session ids, and a Write to the archive comes back
`"archive.jsonl is append-only (cairn invariant)"`.

## What Cairn executes on your machine

The first question you should ask of any plugin that installs hooks:

- **What runs:** small python3 scripts — readable in [`templates/hooks/`](templates/hooks/)
  before install and in your instance's `.claude/` after. Nothing obfuscated, nothing compiled,
  stdlib only.
- **When:** only inside instance directories you scaffolded. The plugin registers **zero global
  hooks** — nothing runs in your other projects.
- **Network: never.** No script makes a network call. Telemetry is local JSONL you can `cat`, and
  it records metadata only (no prompt content) unless you opt in per instance.
- **One global metadata file:** `~/.cairn/registry.json` — instance names, paths, and
  timestamps only, so `/cairn:list` can show you all your systems. `cat` it any time;
  delete it and instances re-register on their next boot. Still zero global hooks.
- **Leaving:** uninstall the plugin and your instances keep their full runtime (it's
  instance-local). Delete an instance directory and Cairn retains nothing about it.

## The evidence base

Cairn's design was derived from — not decorated with — research. Nine adversarially verified
deep-research rounds (~1,280 subagents across R1–R9; every claim faced a 3-vote refutation panel)
plus a docs-verified platform reference produced [**docs/PRINCIPLES.md**](docs/PRINCIPLES.md): 24
principles, each graded **VERIFIED / PREPRINT / BET / REFUTED** and annotated with a
perishability class and verified date, each traceable to primary sources — context-rot studies,
the MemGPT→HMO memory lineage, instruction-drift experiments, the MAST failure taxonomy, METR
time-horizon and pass^k reliability work, the Goodhart/specification-gaming literature, Horvitz
mixed-initiative and automation-bias human factors, LLM-as-judge calibration studies,
living-systematic-review epistemics, orchestration/cascade economics, north-star/guardrail metric
frameworks, and the HCI abandonment research. A traceability audit maps every principle's
commitments to their implementation sites — the four gaps it found were closed, not filed.

Three things make this unusual:

- **The refuted claims ship too.** 80+ plausible-sounding claims that *failed* verification
  (turn-count cliffs, heterogeneous cheap-model swarms beating strong models, fixed failure-mode
  percentages, unscoped chain-of-thought judging gains, "filesystem as sole source of truth") are
  recorded as do-not-build-on negatives — and the design routes around them.
- **Bets are labeled.** Where the literature was empty (drift detection, cap values), the spec
  says **[BET]** and names the telemetry that would settle it — no fake certainty.
- **The raw research is in the repo** ([docs/research/](docs/research/)), so you can audit any
  claim back to its sources.

Design spec: [docs/superpowers/specs/](docs/superpowers/specs/) ·
Implementation plan: [docs/superpowers/plans/](docs/superpowers/plans/)

## Status

`v0.7.1` — the level-zero umbrella is complete on top of the 0.1.0 kernel (92 tests; every
component built TDD with two-stage adversarial review): **SP1** vendored research engine (0.3.0)
→ **SP2** level-zero doctrine, P1–P24 (0.4.0) → **SP3** builder/governor wiring — census,
data-access ladder, pass^k probes, failure-mode telemetry, four deterministic sweeps, boundary
contract (0.5.0) → **SP4** `/cairn:audit` + traceability gap closure (0.6.0) → **SP5**
`SYSTEM-MAP.md` source-of-truth flows (0.7.0), hardened over two adversarial passes (0.7.1).
Still ahead of the public-public bar the spec prescribes: dogfood migration of a real system, one
greenfield build, and a telemetry soak.

Contributions: see [CONTRIBUTING.md](CONTRIBUTING.md). If Cairn worked (or didn't) for you, the
[instance-stats issue template](.github/ISSUE_TEMPLATE/instance-stats.md) lets you share your
locally-computed numbers — nothing is ever collected automatically.

## License

MIT
