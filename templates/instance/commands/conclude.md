---
description: Conclude this cairn instance successfully (habit internalized / goal reached)
---
<!-- managed-by-cairn: {{cairn_version}} -->
The user is done with this system — treat conclusion as success (P13: abandonment can signal diminishing returns, i.e., the habit stuck).

1. Ask for a one-paragraph closing summary in the user's own words (what it did for them; what stuck).
2. Append it (from the instance root): `python3 .claude/hooks/cairn_event.py concluded summary="<their words>"`
3. Write a final section in `state/HOT.md`: "# Concluded <date>" + the summary; refresh `Last reconciled:`.
4. Set `"concluded": true` inside the `instance` object in `manifest.json` (Edit).
5. Commit. The directory stays a plain readable git repo forever — nothing else to do.
