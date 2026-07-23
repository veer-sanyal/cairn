---
description: Log intent, outcome, or a metric observation to cairn telemetry
---
<!-- managed-by-cairn: {{cairn_version}} -->
Log a telemetry event for this session. Ask the user (or infer from the current conversation) which of these applies, then run the matching command via Bash:

- Starting work: `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/cairn_event.py" intent intent=<one of: {{intents}}> note="<short>"`
- Finished something: `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/cairn_event.py" outcome outcome=<done|partial|friction> note="<short>"` (friction requires note stating the friction)
- Something went wrong: `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/cairn_event.py" friction failure_mode=<spec|verify|context|overreach|tooling|upkeep> note="<what happened>"` (spec=did the wrong thing · verify=a check missed it or none ran · context=lost/stale state · overreach=acted past the autonomy line · tooling=data path broke · upkeep=the system demanded too much)
- Metric observation: `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/cairn_event.py" metric name=<metric> value=<value>`
- Typing an earlier lapse: `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/cairn_event.py" lapse cause=<forgot|upkeep|skipped|suspended>`

One event per real thing — don't ceremonially log. If an upkeep lapse gets typed, note it prominently: upkeep burden is a kernel bug, not a user failing (P13).
