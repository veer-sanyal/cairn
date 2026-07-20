---
description: Honorably pause this keel instance (typed, recoverable — not failure)
---
The user wants to pause this system. This is a first-class, recoverable state (P13) — no guilt framing, ever.

1. Ask (briefly) which cause fits: taking a break (`skipped`), too much upkeep (`upkeep`), life moved on for now (`suspended`).
2. Run: `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/keel_event.py" lapse cause=<cause> deliberate=true`
3. Update `state/HOT.md` with a one-line "Suspended <date>: <cause>" note and refresh `Last reconciled:`.
4. Commit. Tell the user the boot banner will greet them with "what changed", whenever they return — no streaks were harmed.
