# Cairn

> A cairn is a hand-stacked trail marker. It survives the seasons, asks nothing of you,
> and when you come back — after a week, after a month — it shows you exactly where you
> left off. That's what this plugin builds.

Cairn is a [Claude Code](https://claude.com/claude-code) plugin that interviews you and
scaffolds a **long-lived personal agentic system** — a study coach, a job-search tracker,
a training log, a writing practice, any domain that needs memory, honesty, and months of
your real life. Not a coding framework: a kernel for systems about *you*.

Under the hood it works like a systems engineer, not a template dispenser: a bundled
**level-zero doctrine** (24 evidence-graded principles about how agentic systems fail,
how objectives resist corruption, where the human boundary sits, when knowledge expires),
a **vendored research engine** that manufactures the domain-specific knowledge each
instance needs at build time, and an **environment census** of what your machine can
actually do — so it can design, probe, and govern a system for problems it has never
seen before. It can also [audit an agentic setup you already have](#what-you-get).

**Before:** you ask Claude to help you study; three weeks later the folder is a graveyard
of stale notes and you're re-explaining everything from scratch.

**After `/cairn:build`:** a ~15-minute interview scaffolds a study coach with its own
memory discipline, a success metric *you wrote in your own words*, and a monthly review
that only proposes changes your usage data justifies — and when you come back after a
break it greets you with *"here's where things stand"*, never a broken streak.

## Install

```
/plugin marketplace add veer-sanyal/cairn
/plugin install cairn
```

Then, in an empty directory:

```
/cairn:build
```

Requires macOS/Linux and python3 (stdlib only — no pip installs). Windows is not
supported in v1.

## What you get

Every instance Cairn scaffolds is an ordinary directory + git repo that works with plain
Claude Code — the plugin is a dependency, not a cage:

```
your-instance/
  CLAUDE.md              # thin router: what this system is, where each fact lives
  manifest.json          # metric contract, boundary contract, census, every decision with its grade
  docs/
    SYSTEM-MAP.md        # every flow as mermaid — the system's source of truth
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

| Command | What it does |
|---|---|
| `/cairn:build` | Interview → metric contract → scaffold. Shows you drafts and iterates; **you** author the goals, it only refines them. |
| `/cairn:research` | The research engine: frames a decision, runs a claim-scaled 3-vote adversarial deep-research workflow, persists graded findings (with refresh-by dates) into the instance's `docs/RESEARCH.md`. Used by build and review; callable directly. |
| `/cairn:audit` | Diagnose an existing (non-Cairn) agentic setup against the doctrine: measured boot cost, missing metric contract, census + ladder upgrades, verification gaps — blast-ordered BUILD/PARK/REJECT fixes, or migrate via a pre-filled `/cairn:build`. |
| `/cairn:review` | The governor: re-validates invariants, consolidates memory (probe → verify → repair), reports your metrics, and proposes changes as **BUILD / PARK / REJECT** — you are the gate. |
| `/cairn:upgrade` | Migrates an instance to a new kernel version. Never overwrites a file you've modified — new versions land alongside as `.cairn-new`. |
| `/log` `/suspend` `/conclude` | Instance-local. Log intent/outcome/metrics; pause honorably; or conclude — **concluding is a success state**, not churn. |

## The four ideas

**1. A metric contract, or no instance.**
The interview won't scaffold until you've declared — in your own words — a north star
(watched, never chased), the input levers your daily use actually moves, and guardrail
metrics with hard limits. Reviews act on inputs and guardrails; the north star is the
thing they protect. Every instance also carries standing anti-bloat guardrails (boot
context cost, upkeep burden) that no proposed change may regress.

**2. Lapses are typed, recoverable, and never shamed.**
The abandonment research is unambiguous: people stop tracking for four distinct reasons —
forgetting, upkeep burden, deliberate skipping, suspending — and lapsing is usually
temporary. So Cairn types every lapse instead of flagging churn, treats **upkeep lapses
as kernel bugs** (the system demanded too much writing — that's Cairn's fault, not
yours), ships no streaks and no guilt screens, and makes `/conclude` first-class: a
system you outgrew because the habit stuck is a *win*, and the telemetry can tell that
apart from decay.

**3. Self-improvement with a human gate.**
Models reviewing their own work without external feedback measurably get *worse* — so
nothing in Cairn self-applies. Reviews must cite your telemetry events (no vibes
features), proposals arrive as BUILD / PARK / REJECT for you to decide, and the kernel
itself only changes through versioned releases you explicitly upgrade to.

**4. Knowledge is manufactured, graded, and expires on schedule.**
The kernel knows *methods* (level-zero doctrine: failure taxonomy, Goodhart resistance,
orchestration economics, the human-agent boundary); it never pretends to know your
domain. Domain knowledge is produced per instance by a claim-scaled, 3-vote adversarial
research engine, persisted with evidence grades and **perishability classes** — and
because models can't feel their own knowledge going stale (~55%, a coin flip), expiry is
structural: refresh-by dates, census diffs, and an unconditional annual ceiling that the
governor sweeps deterministically.

## Enforced, not requested

Long-conversation instruction drift is real and large (~39% average performance drop
across 15 models in multi-turn studies), which is why Cairn's invariants are **hooks,
not prose**: file-size caps that keep your router lean, an append-only archive, guarded
overwrites of memory files, a session banner that reconciles reality before work. Hooks
fail soft — a broken script warns, it never bricks a session — and every invariant is
re-validated post-hoc at review, because hooks can't see edits made outside Claude Code.

Verified live, not just in tests: the boot banner reaches the model, session telemetry
writes with real session ids, and a Write to the archive comes back
`"archive.jsonl is append-only (cairn invariant)"`.

## What Cairn executes on your machine

The first question you should ask of any plugin that installs hooks:

- **What runs:** small python3 scripts — readable in [`templates/hooks/`](templates/hooks/)
  before install and in your instance's `.claude/` after. Nothing obfuscated, nothing
  compiled, stdlib only.
- **When:** only inside instance directories you scaffolded. The plugin registers
  **zero global hooks** — nothing runs in your other projects.
- **Network: never.** No script makes a network call. Telemetry is local JSONL you can
  `cat`, and it records metadata only (no prompt content) unless you opt in per instance.
- **Leaving:** uninstall the plugin and your instances keep their full runtime (it's
  instance-local). Delete an instance directory and Cairn retains nothing about it.

## The evidence base

Cairn's design was derived from — not decorated with — research. Nine adversarially
verified deep-research rounds (~1,280 subagents across R1–R9; every claim faced a 3-vote
refutation panel) plus a docs-verified platform reference produced
[**docs/PRINCIPLES.md**](docs/PRINCIPLES.md): 24 principles, each graded
**VERIFIED / PREPRINT / BET / REFUTED** and annotated with a perishability class and
verified date, each traceable to primary sources — context-rot studies, the MemGPT→HMO
memory lineage, instruction-drift experiments, the MAST failure taxonomy, METR
time-horizon and pass^k reliability work, the Goodhart/specification-gaming literature,
Horvitz mixed-initiative and automation-bias human factors, LLM-as-judge calibration
studies, living-systematic-review epistemics, orchestration/cascade economics,
north-star/guardrail metric frameworks, and the HCI abandonment research. A traceability
audit maps every principle's commitments to their implementation sites — the four gaps it
found were closed, not filed.

Three things make this unusual:

- **The refuted claims ship too.** 80+ plausible-sounding claims that *failed*
  verification (turn-count cliffs, heterogeneous cheap-model swarms beating strong
  models, fixed failure-mode percentages, unscoped chain-of-thought judging gains,
  "filesystem as sole source of truth") are recorded as do-not-build-on negatives — and
  the design routes around them.
- **Bets are labeled.** Where the literature was empty (drift detection, cap values),
  the spec says **[BET]** and names the telemetry that would settle it — no fake
  certainty.
- **The raw research is in the repo** ([docs/research/](docs/research/)), so you can
  audit any claim back to its sources.

Design spec: [docs/superpowers/specs/](docs/superpowers/specs/) ·
Implementation plan: [docs/superpowers/plans/](docs/superpowers/plans/)

## Status

`v0.7.0` — the level-zero umbrella is complete on top of the 0.1.0 kernel (92 tests;
every component built TDD with two-stage adversarial review): **SP1** vendored research
engine (0.3.0) → **SP2** level-zero doctrine, P1–P24 (0.4.0) → **SP3** builder/governor
wiring — census, data-access ladder, pass^k probes, failure-mode telemetry, four
deterministic sweeps, boundary contract (0.5.0) → **SP4** `/cairn:audit` + traceability
gap closure (0.6.0) → **SP5** `SYSTEM-MAP.md` source-of-truth flows (0.7.0).
Still ahead of the public-public bar the spec prescribes: dogfood migration of a real
system, one greenfield build, and a telemetry soak.

Contributions: see [CONTRIBUTING.md](CONTRIBUTING.md). If Cairn worked (or didn't) for
you, the [instance-stats issue template](.github/ISSUE_TEMPLATE/instance-stats.md) lets
you share your locally-computed numbers — nothing is ever collected automatically.

## License

MIT
