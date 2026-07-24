---
name: audit
description: Diagnose an existing (non-Cairn) agentic system against the level-zero doctrine — census diff, taxonomy walk, north-star elicitation — and emit a blast-ordered BUILD/PARK/REJECT fix list
---

# /cairn:audit — the diagnostician

Run from inside an existing agentic system's directory (a Claude Code setup: CLAUDE.md,
skills, hooks, MCP config, memory files). Doctrine references are P-refs into
${CLAUDE_PLUGIN_ROOT}/docs/PRINCIPLES.md — cite them, never restate them.

## Stage 0 — Identify what this is

If `manifest.json` with `cairn_version` exists: STOP — this is a cairn instance; run
/cairn:review instead (the governor knows this system's telemetry; the audit doesn't).

Otherwise map the repo to mechanisms (P23): what loads every session (CLAUDE.md, anything
referenced from it, always-resident rules — MEASURE the bytes via `wc -c`, don't estimate),
what loads on demand (skills, docs), what fires deterministically (hooks — read
.claude/settings.json), what external tools it assumes (MCP config, hardcoded URLs/paths in
skills). If `AUDIT.md` exists from a prior run, read it FIRST — a finding the user
previously REJECTed only resurfaces citing evidence newer than the rejection (same
anti-re-litigation rule as the governor).

**Map first.** If `docs/SYSTEM-MAP.md` exists, read it and drift-check it against reality:
flows referencing removed skills/hooks, mechanisms present in the repo but missing from the
map — drift is a finding (the map lied). If it does not exist, reconstructing it IS the
audit's first deliverable: walk every entry point (hooks, commands, skills, scheduled jobs)
and write one flow section per workflow (stable id, Trigger · Writes · Verification ·
Boundary metadata line, mermaid block, `Last reconciled:` stamp) BEFORE the doctrine walk —
then the walk cites flow ids, and the map stays with the repo as the source of truth either
way.

## Stage 1 — Elicit the north star (P14, P12)

Interview, artifact-driven: show what you found in Stage 0 and ask what this system is FOR —
in the user's own words — and what "working" would look like. Then: does anything measure
that today? Refine wording, never author the goal for them (P14). Most existing systems
have no metric contract; its absence is finding #1, not a blocker. If they can't state a
north star, that IS the audit's headline: the system has no way to know whether it works.

## Stage 2 — Census & data paths (P23; the build skill's Stage 1.5 protocol)

Enumerate the environment: session MCP servers/tools, `claude mcp list` via Bash where
available, surfaces (Chrome, computer use). Infer the system's data needs from its skills
and files, place each on the data-access ladder (1 connected MCP/API → 2 installable
connector, manual-assisted → 3 browser automation → 4 screenshot+vision → 5 manual entry),
and flag upgrades: a skill that screenshots a dashboard when a connector for it exists is a
rung-4-to-rung-1 finding.

## Stage 3 — Doctrine walk (evidence or it didn't happen)

Diagnose against the principles. HARD RULE: every finding carries BOTH a principle ref AND
observed evidence at file:line (or a measured number). No vibes findings.

- **Boot cost & distractors (P1, P4):** resident bytes measured in Stage 0; name content
  that boots every session but is rarely needed — it actively hurts, it isn't neutral.
- **Memory discipline (P2, P5):** facts that live only in conversation history or in one
  giant file; no archive tier; stale files with no dates or reconciliation stamps.
- **Verification gaps (P16, P21):** checks that run but verify nothing ("compiles" ≠
  "works"); no external correction loop — agents rarely self-correct; outputs consumed
  without any pass^k evidence the model can do the task reliably (P17).
- **Orchestration (P20):** fan-out where single-threaded is right (or the reverse);
  multiple writers to shared state; expensive-model calls where a cascade would do.
- **Goodhart exposure (P18):** any metric that is chased AND unguarded; proxy metrics with
  no revalidation date.
- **Boundary (P19):** irreversible or outward-facing actions with no gate; confirmation
  prompts on everything (rubber-stamp training); no ask discipline at all.
- **Knowledge staleness (P22):** cached domain knowledge with no date, no refresh
  discipline, no structural expiry — undated knowledge is a BET wearing a VERIFIED badge.

Where a finding's fix depends on contested domain evidence, note it as a candidate for a
/cairn:research run rather than guessing.

## Stage 4 — Report, gate, disposition

Present findings as BUILD / PARK / REJECT proposals, blast-ordered largest-first (P19
ask-order), each with 2-3 options and a recommended default (advise, don't menu). The user
is the gate — nothing is applied unasked.

**Research-backed fixes.** A finding whose right fix depends on contested domain evidence
becomes a proposal whose FIRST step is a research run, not a guessed parameter — apply the
build skill's four-clause research bar (load-bearing ∧ contested ∧ generalizable evidence
plausibly exists ∧ narrow enough for one run); most findings won't clear it and shouldn't.
When it clears: run /cairn:research using the PLUGIN's copies (this repo has no installed
engine — Workflow scriptPath ${CLAUDE_PLUGIN_ROOT}/skills/research/deep-research.js, persist
via ${CLAUDE_PLUGIN_ROOT}/templates/hooks/doctrine_write.py into THIS repo's
docs/RESEARCH.md), then parametrize the fix citing the finding — a refuted or unverified
claim never becomes a parameter, same rule as the builder.

Then offer three dispositions:
1. **Apply agreed fixes in place.** Boundary contract applies even though this repo has
   none: git commit checkpoint FIRST — refuse to edit a dirty tree without the user's
   explicit say-so; reversible file edits proceed (show the diff); restructuring asks
   first; never delete user content — demote or move only.
2. **Write `AUDIT.md`** into the repo: every finding with evidence, principle ref, and the
   user's decision — the trail survives for the next run's anti-re-litigation rule.
   Note in AUDIT.md that any docs/RESEARCH.md Refresh-by dates created here are swept only
   inside a cairn instance — without migration (disposition 3), re-research happens at the
   next audit, not automatically.
3. **Migrate to a cairn instance:** hand off to /cairn:build with a pre-filled draft —
   north star from Stage 1, census and data_paths from Stage 2, existing files mapped to a
   proposed owner plan — so the interview starts from evidence, not zero. Migration copies;
   it never destroys the source repo.
