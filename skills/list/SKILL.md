---
name: list
description: Portfolio view of every cairn instance on this machine — status, routing by name, read-only peeks into another instance
---

# /cairn:list — the registry

The global registry (`~/.cairn/registry.json`, or `$CAIRN_HOME/registry.json`) is a
rebuildable cache of instance pointers — names, paths, timestamps, never state. Instances
maintain it themselves at scaffold and every boot. Everything durable lives in each
instance's own files; this skill only ever READS instances.

## Portfolio view (default)

Run:

    python3 "${CLAUDE_PLUGIN_ROOT}/skills/list/list_instances.py" --json

Render one table from the JSON: **name · purpose · status · last session · last reconciled**.
Rules:
- Status is computed by the script (concluded ← manifest flag; suspended ← deliberate
  suspend lapse with no session start after it; else active). Do not re-derive it.
- Names may collide — when two entries share a name, show the path to disambiguate.
- **Never guilt (P13):** report status plainly. No "neglected for N days", no streaks,
  no nudges to return. A suspended or concluded system is an honorable state.
- An entry with status `missing` renders as "missing — moved or deleted?". Offer removal;
  only on explicit user confirmation run:
      python3 "${CLAUDE_PLUGIN_ROOT}/skills/list/list_instances.py" --prune "<path>"
  The user is the gate. Never auto-prune.
- If the current working directory is inside a cairn instance that is NOT in the registry
  (pre-0.8.0 instance), offer once: "register this instance?" On yes:
      python3 "${CLAUDE_PLUGIN_ROOT}/skills/list/list_instances.py" --register "<root>"
  Never walk the filesystem looking for unregistered instances.

## Routing ("open my job system")

Resolve the user's phrase against `name` and `purpose` (substring match, case-insensitive).
- One match → hand over the path: "your job-search instance is at <path> — open a session
  there to work in it."
- Multiple matches → show the candidates, the user picks.
- Routing is resolution, NOT teleportation: an instance's hooks, banner, and telemetry
  exist only in a session opened in its own directory. Never simulate working inside
  another instance from here; offer a peek instead if they just want to know where
  things stand.

## Peeks (read-only, P3)

When the user asks what another instance says / where it stands:
1. Resolve it via the registry (routing rules above).
2. Spawn a subagent that reads ONLY that instance's `state/HOT.md` and `manifest.json`
   and returns a condensed summary (~1-2K tokens): where things stand, north star, status.
3. Relay the summary. The other instance's files never enter this session's main context.

Hard rule: peeks never write. Not files, not telemetry, nothing — the target instance's
history must not show a session it didn't have. If a peek is asked to change something
("mark my job system suspended"), decline and route instead: that action belongs to a
session opened in that instance. Overreach is a telemetry-visible failure mode
(`failure_mode=overreach`) — log it in the CURRENT instance if you catch yourself.
