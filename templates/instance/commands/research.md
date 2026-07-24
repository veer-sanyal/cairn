---
description: Framed research front door — directing-research fires FIRST (name the decision, right-size, GROUND), then the engine only if warranted
---
<!-- managed-by-cairn: {{cairn_version}} -->
This is the **mandatory front door** for any research in this instance. The directing-research
discipline fires FIRST, every time — before a single search. **Never launch
`.claude/workflows/deep-research.js` raw**; framing is what decides whether the engine even runs,
and at what size. Research serves a decision, not a topic.

## Step 1 — Frame (fires first, never skipped)

Write down, before searching anything:
- **The decision this informs.** Which parameter, design choice, or proposal changes based on
  the answer? If you can't name one, STOP — it doesn't clear the research bar; answer plainly or
  drop it. (No decision → no research.)
- **The real question**, restated in your own words and scoped to that decision — widen if the
  decision hinges on an adjacent question, narrow if the topic is broader than the need.
- **What's already settled** — read `docs/RESEARCH.md` and `manifest.json` first; never
  re-research a finding that is current and VERIFIED.
- If the domain is unfamiliar, run 1–3 orientation searches to map terms — reconnaissance only,
  not findings. 4+ searches means you've started researching unverified; stop and route to depth.

## Step 2 — Right-size (this is the gate the framing exists to apply)

Scale effort to the question — more compute amplifies confident noise unless you can select the
right answer:
- **Already known, or a single fact** → just answer / one search. Do NOT launch the engine.
- **A comparison or a few angles** → a handful of targeted WebSearches; spot-verify. No engine.
- **Broad, contested, decision-critical, or multi-source** → launch the full engine (Step 3).

## Step 3 — Launch the engine (only if Step 2 says so)

Write the GROUNDING block, then launch this instance's own vendored engine:

```
<framed question — the decision it serves, in one or two sentences>

GROUNDING:
- Breadth: narrow | standard | broad
- Sub-areas needing verified coverage: <each distinct area; each gets its own angle + verification floor>
- Key terms/entities: <names, jargon, synonyms that make queries land>
- Known primary sources worth fetching: <papers, specs, official docs>
- Already known / do not research: <settled knowledge the engine should skip>
```

`Workflow({ scriptPath: ".claude/workflows/deep-research.js", args: "<framed question + GROUNDING>" })`

Backgrounded — continue other work and return when the result notification arrives; save the
result JSON to a temp file. If the Workflow tool is unavailable (needs Pro+/API, can be disabled),
fall back to the degraded pass: 2–5 angle subagents, then 3 adversarial verifiers per load-bearing
claim prompted to REFUTE (≥2 refutations kill it), and cap every grade at THIN.

## Step 4 — Persist (unpersisted research didn't happen)

```
python3 .claude/hooks/doctrine_write.py <result.json> . \
  --domain "<short domain name>" --perishability <durable|semi-durable|perishable>
```

Grades: engine confidence high → VERIFIED, medium/low → THIN (degraded mode caps at THIN).
Refuted claims land in the "Refuted — do not build on" section — cite them to kill zombie
parameters, never to justify one. Every research-backed parameter cites its finding from the
manifest `decisions[]` entry.
