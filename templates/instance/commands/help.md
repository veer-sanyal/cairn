---
description: Explain what this system is, how to use it, and how it helps you — and answer questions about it
---
<!-- managed-by-cairn: {{cairn_version}} -->
The user wants to understand this cairn instance — what it is, how it helps them, how to use it day to day, or a specific question about it. Orient them from the instance's OWN live state, not from generic cairn knowledge.

1. **Read the live sources first (don't guess):** `manifest.json` (the metric contract — north star, input levers, guardrails; cadence; boundary/ask-budget; triggers; intents), `README.md` (the overview), `docs/MANUAL.md` (the how-to reference), and `state/HOT.md` (where things stand right now). The manifest is authoritative — if a doc and the manifest disagree, trust the manifest and mention the doc looks stale.
2. **If they asked something specific** (what's my north star? why did the last review flag X? how do I record Y? is a quiet week bad?), answer THAT first, briefly, from the manifest/telemetry — then offer to go wider.
3. **Otherwise give a short, plain-language orientation** in their domain's terms:
   - **What this system is for** — the one-line purpose.
   - **The metric tree, in plain words** — the north star ({{north_star_name}}) is *watched, never chased* (P12): the outcome you're moving toward, not a number to game. The **input levers** are what your daily use actually moves — the real dials. The **guardrails** are hard limits the review flags if crossed. Name each from the manifest and say what it means for THEM.
   - **How you actually use it** — start work → `/log` intent; finish → `/log` outcome; something felt off → `/log` friction; life got in the way → `/suspend` (honorable, no shame); goal reached or habit stuck → `/conclude` (a success); periodic check-in → `/cairn:review`.
   - **How it helps** — it remembers across months, boots you with "where things stand," proposes changes only from your own telemetry (never nags on a broken streak), and treats a lapse as typed and recoverable, not failure.

Keep it human and short — this is orientation, not a doctrine lecture. Cite a P-ref only if they ask *why* something works the way it does. Point them at `docs/MANUAL.md` for the full reference.
