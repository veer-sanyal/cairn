---
name: research
description: Frame a decision, run the vendored deep-research engine (claim-scaled, 3-vote adversarial), and persist graded findings into the instance's docs/RESEARCH.md
---

# /cairn:research — the research engine

Research serves a **decision, not a topic**. This skill is the mandatory front door to the
engine: the builder (Stage 2.5) and the governor (research proposals) route through this
procedure — never launch the workflow raw.

## Step 1 — Frame (never skip)

Before searching anything, write down:
- **The decision this informs.** Which parameter, design choice, or proposal will change
  based on the answer? If you can't name it, stop — it doesn't clear the research bar.
- **The real question**, restated in your own words, scoped to the decision (widen if the
  decision hinges on an adjacent question; narrow if the topic is broader than the need).
- **What's already settled** — check docs/RESEARCH.md and the manifest first; never
  re-research a finding that is current and VERIFIED.
- If the domain is unfamiliar or fast-moving, run 1-3 orientation searches to map terms —
  reconnaissance only, never findings. 4+ searches means you've started researching
  unverified; stop and launch the engine instead.

## Step 2 — Write the GROUNDING block

```
<framed question — the decision it serves, in one or two sentences>

GROUNDING:
- Breadth: narrow | standard | broad   (be honest — padding narrow questions wastes verification budget)
- Sub-areas needing verified coverage: <each distinct area; each gets its own angle and a verification floor>
- Key terms/entities: <names, jargon, synonyms that make queries land>
- Known primary sources worth fetching: <papers, specs, official docs>
- Already known / do not research: <settled knowledge the engine should skip>
```

The engine sizes the whole run from this (2-8 angles, fetch budget, per-angle verification
floors). A missing GROUNDING block makes it guess from the question text alone.

## Step 3 — Launch

Inside a cairn instance (the normal case — governor re-research, post-scaffold builder runs):

```
Workflow({ scriptPath: ".claude/workflows/deep-research.js", args: "<framed question + GROUNDING>" })
```

From the plugin before an instance exists (builder Stage 2.5, pre-scaffold):

```
Workflow({ scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/research/deep-research.js", args: "<framed question + GROUNDING>" })
```

The run is backgrounded; continue interview work and return when the result notification
arrives. Save the result JSON to a temp file when it completes.

## Step 4 — Persist (the engine contract)

Every run's output is persisted through the deterministic writer — findings never live only
in conversation:

```
python3 .claude/hooks/doctrine_write.py <result.json> <instance-root> \
  --domain "<short domain name>" --perishability <class>
```

(Pre-scaffold, use `${CLAUDE_PLUGIN_ROOT}/templates/hooks/doctrine_write.py` and persist into
the instance directory as soon as it is scaffolded.)

Choose the perishability class honestly — it sets the Refresh-by date the governor sweeps:
- **durable** — mechanisms, human-factors results, math ("on contradiction")
- **semi-durable** — taxonomies' magnitudes, tooling economics (~180 days)
- **perishable** — model capabilities, platform surface, prices (~60 days)

Grades are the instance vocabulary: engine confidence high → **VERIFIED**, medium/low →
**THIN**. Refuted claims land in a "Refuted — do not build on" section — cite them to kill
zombie parameters, never to justify one. Every research-backed parameter cites its finding
from the manifest decisions[] entry (build Stage 2.5 rule, unchanged).

## Degraded mode (no Workflow tool)

Workflows need Pro+/API and can be disabled. If the Workflow tool is unavailable or the
launch is denied:
1. Spawn one general-purpose subagent per GROUNDING sub-area (2-5 total): WebSearch that
   angle, fetch the 2-3 strongest sources, extract falsifiable claims with quotes.
2. For each load-bearing claim, spawn 3 adversarial verifier subagents prompted to REFUTE
   it against sources; ≥2 refutations kill the claim. Default-refute when uncertain.
3. Persist survivors through doctrine_write.py exactly as above, but cap every grade at
   **THIN** — the degraded pass verifies at reduced scale and must not masquerade as the
   full engine. Say so in the section's caveats.

You hand-build the result.json the engine would have produced — this exact shape:

```json
{"findings": [{"claim": "<surviving claim>", "confidence": "medium",
               "sources": ["<url>", "<url>"], "vote": "3-0"}],
 "confirmed": [],
 "refuted": [{"claim": "<killed claim>", "vote": "0-3", "source": "<url>"}],
 "caveats": "degraded mode: reduced-scale verification, grades capped at THIN"}
```

doctrine_write maps confidence → grade: `high` → VERIFIED, `medium`/`low` → THIN.
"Cap at THIN" therefore means: never write `confidence: "high"` in degraded mode — use
`medium` for the strongest survivors.

## Contract summary

**In:** a framed decision + GROUNDING block. **Out:** graded findings + refuted list +
caveats appended to `docs/RESEARCH.md`, date-stamped, with a perishability class and
Refresh-by date the governor can sweep. No exceptions: unpersisted research didn't happen.
