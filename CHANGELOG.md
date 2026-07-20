# Changelog

## 0.1.0 — initial kernel, builder, governor, upgrade

- **Kernel runtime** — instance-local `python3` hooks: SessionStart boot banner (validator + telemetry gap look-back + trigger rules), SessionEnd session record, PreToolUse Write/Edit and Bash invariant guards. All fail-soft (exit 0; deliberate blocks are JSON `permissionDecision: deny`).
- **Validator** — the "lint": size caps, HOT.md staleness stamp, JSONL integrity, stale review sentinel; `--json` output reused by `/cairn:review`.
- **Telemetry** — local append-only `events.jsonl` via `cairn_lib` + `cairn_event.py`; typed `session`/`lapse`/`intent`/`outcome`/`metric`/`proposal` events, no network.
- **Instance templates** — thin-router `CLAUDE.md`, `HOT.md`, hook-wired `settings.json`, and instance-local `/log` `/suspend` `/conclude` commands.
- **Scaffolder** (`skills/build/scaffold.py`) — deterministic build-config → complete instance generator.
- **Builder** (`/cairn:build`) — artifact-driven interview: user-authored goals, metric contract, if-then compilation onto the closed trigger menu.
- **Governor** (`/cairn:review`) — validator re-pass, memory-lane consolidation (SKIP/MERGE/INSERT), telemetry-cited BUILD/PARK/REJECT proposals with the user as gate.
- **Upgrade** (`/cairn:upgrade` + `merge.py`) — version migration with changelog diff and no-silent-data-loss managed-file merge.
- **Evidence base** — `docs/PRINCIPLES.md`, design spec, and raw verified research shipped with the plugin.

Known v1 deferrals: recall-count demotion (recency-only shipped, [BET]); `/cairn:contribute` upstream learning (opt-in issue template instead); Windows (declared unsupported).
