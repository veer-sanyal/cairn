# Cairn

> A cairn is a hand-stacked trail marker. It survives the seasons, asks nothing of you,
> and when you come back — after a week, after a month — it shows you exactly where you
> left off. That's what this plugin builds.

Cairn is a [Claude Code](https://claude.com/claude-code) plugin that interviews you and
scaffolds a **long-lived personal agentic system** — a study coach, a job-search tracker,
a training log, a writing practice, any domain that needs memory, honesty, and months of
your real life. Not a coding framework: a kernel for systems about *you*.

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
  manifest.json          # your metric contract + every design decision, with its evidence grade
  state/
    HOT.md               # lean "where things stand" snapshot — boots every session
    working/             # topic files, loaded on demand
    archive.jsonl        # append-only history (hook-enforced)
  telemetry/
    events.jsonl         # local-only usage log — cat it any time
  .claude/
    hooks/               # the kernel runtime, copied INTO your instance
    commands/            # /log, /suspend, /conclude — yours even if you uninstall Cairn
```

| Command | What it does |
|---|---|
| `/cairn:build` | Interview → metric contract → scaffold. Shows you drafts and iterates; **you** author the goals, it only refines them. |
| `/cairn:research` | The research engine: frames a decision, runs a claim-scaled 3-vote adversarial deep-research workflow, persists graded findings (with refresh-by dates) into the instance's `docs/RESEARCH.md`. Used by build and review; callable directly. |
| `/cairn:audit` | Diagnose an existing (non-Cairn) agentic setup against the doctrine: measured boot cost, missing metric contract, census + ladder upgrades, verification gaps — blast-ordered BUILD/PARK/REJECT fixes, or migrate via a pre-filled `/cairn:build`. |
| `/cairn:review` | The governor: re-validates invariants, consolidates memory (probe → verify → repair), reports your metrics, and proposes changes as **BUILD / PARK / REJECT** — you are the gate. |
| `/cairn:upgrade` | Migrates an instance to a new kernel version. Never overwrites a file you've modified — new versions land alongside as `.cairn-new`. |
| `/log` `/suspend` `/conclude` | Instance-local. Log intent/outcome/metrics; pause honorably; or conclude — **concluding is a success state**, not churn. |

## The three ideas

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

Cairn's design was derived from — not decorated with — research. Four adversarially
verified deep-research rounds (~415 subagents; every claim faced a 3-vote refutation
panel) produced [**docs/PRINCIPLES.md**](docs/PRINCIPLES.md): 15 principles, each graded
**VERIFIED / PREPRINT / BET / REFUTED**, each traceable to primary sources — context-rot
studies, the MemGPT→HMO memory lineage, multi-turn instruction-drift experiments, the
self-correction failure literature, OpenTelemetry GenAI conventions, north-star/guardrail
metric frameworks, and the HCI abandonment research.

Three things make this unusual:

- **The refuted claims ship too.** 21+ plausible-sounding claims that *failed*
  verification (turn-count cliffs, popular abandonment statistics, "filesystem as sole
  source of truth") are recorded as do-not-build-on negatives — and the design routes
  around them.
- **Bets are labeled.** Where the literature was empty (drift detection, cap values),
  the spec says **[BET]** and names the telemetry that would settle it — no fake
  certainty.
- **The raw research is in the repo** ([docs/research/](docs/research/)), so you can
  audit any claim back to its sources.

Design spec: [docs/superpowers/specs/](docs/superpowers/specs/) ·
Implementation plan: [docs/superpowers/plans/](docs/superpowers/plans/)

## Status

`v0.1.0` — kernel, builder, governor, and upgrade path built and reviewed (53 tests;
every component adversarially code-reviewed, 8 review-caught bugs fixed pre-release).
Currently in the validation phase the spec prescribes: dogfood migration of a real
system, one greenfield build, and a telemetry soak before this repo goes public-public.

Contributions: see [CONTRIBUTING.md](CONTRIBUTING.md). If Cairn worked (or didn't) for
you, the [instance-stats issue template](.github/ISSUE_TEMPLATE/instance-stats.md) lets
you share your locally-computed numbers — nothing is ever collected automatically.

## License

MIT
