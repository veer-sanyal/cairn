---
description: Honorably pause this cairn instance (typed, recoverable — not failure)
---
<!-- managed-by-cairn: {{cairn_version}} -->
The user wants to pause this system. This is a first-class, recoverable state (P13) — no guilt framing, ever.

1. Ask (briefly) why: taking a break (`skipped`), too much upkeep (`upkeep`), life moved on for now (`other`).
2. Run (from the instance root): `python3 .claude/hooks/cairn_event.py lapse cause=suspended deliberate=true reason=<skipped|upkeep|other>` — cause is ALWAYS `suspended` (that is what /cairn:list reads as "paused"); the user's answer goes in `reason=`.
3. Update `state/HOT.md` with a one-line "Suspended <date>: <reason>" note and refresh `Last reconciled:`.
4. Commit. Tell the user the boot banner will greet them with "what changed", whenever they return — no streaks were harmed.
