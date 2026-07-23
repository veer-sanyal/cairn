# Mechanism-selection & environment-census facts — Claude Code, verified 2026-07-23

Verified against official docs (code.claude.com/docs) by a claude-code-guide docs agent.
Refresh-by: next Cairn release, or on any Claude Code minor-version jump. This file is the
raw verified reference feeding the level-zero mechanism-selection doctrine; grade all items
[VERIFIED — first-party docs] unless marked "not documented".

## 1. Primitive selection matrix

| Primitive | Fires/loads | Context cost | Deterministic? | Choose when |
|---|---|---|---|---|
| Hooks (`settings.json`, plugin `hooks/hooks.json`) | Lifecycle events | Negligible (command hooks); prompt/agent hooks cost tokens | Yes (exit code / JSON) | Guaranteed, non-negotiable enforcement; never judgment calls |
| Skills (`skills/<name>/SKILL.md`) | `/name` or model-invoked (unless `disable-model-invocation: true`) | On-demand only | No | Reusable procedures needing judgment; large/optional content |
| Slash commands (built-in) | Message start | Negligible | Yes | Don't create custom ones — skills subsume legacy `commands/` |
| Subagents (`agents/<name>.md`) | Model-matched to description, or user-invoked | Full isolated window each | No | Side tasks that would bloat main context; tool-restricted work |
| Saved workflows (`.claude/workflows/*.js`) | `/name` or Workflow tool; background | Script vars hold state outside model context | Orchestration yes, agents no | >handful of agents, multi-stage verification, repeatable runs |
| MCP servers (`.mcp.json`) | Tool list at session start; tools on demand | ~100 resident tokens/server | Tool behavior external | External system is source of truth |
| CLAUDE.md | Every session start | Fully resident (500–2000 tok) | No | Facts every session needs; never regenerable content |
| Plugins | On install; components as above | Same as components | Per component | Distribution/versioning of the above |

Decision tree: fires automatically → hook; reusable instruction → skill; context-bloating side task → subagent; many agents/stages → workflow; external tools → MCP; every-session facts → CLAUDE.md; distribution → plugin.

Skill frontmatter keys: `description`, `disable-model-invocation`, `allowed-tools`, `model`, `once`, `argument-hint`.
Subagent frontmatter: `description`, `system-prompt`, `model`, `allowed-tools`, `max-tool-uses`, `allow-skill-invocation`, `use-subagent-for`.
Workflows require Pro+/API; v2.1.154+; disableable via `disableWorkflows: true`.

## 2. Runtime environment enumerability (census feasibility)

- MCP servers: enumerable — `claude mcp list` (CLI), `/mcp` (UI), `system/init` message `mcp_servers` array (SDK). Tool naming `mcp__<server>__<tool>`.
- Tool schemas/details: NOT queryable programmatically (ToolSearch loads on demand in-session, but no external API).
- Skills: discoverable via `slash_commands` in `system/init` (project `/name`, plugin `/plugin:name`).
- Installed plugins: `claude plugin list` CLI only; NOT enumerable from SDK.
- Chrome / computer-use / connectors: no feature-detection API — detect via presence of the corresponding MCP server in `mcp_servers`.

Census design consequence: the builder census = parse `claude mcp list` + slash-command list + probe for surface-specific server names. Tool-level capability must be inferred from server identity, not schema inspection.

## 3. MCP registry / discovery

- No CLI or SDK API to search a connector registry. Discovery is manual/web (mcp.run, modelcontextprotocol GitHub org). (Note: some sessions expose an `mcp-registry` MCP server with search tools — presence varies; treat as census-detected, not guaranteed.)
- Install: `claude mcp add --transport http <name> <url>` or edit `.mcp.json`. Scopes: local / project (`.mcp.json`, committed) / user.
- Plugins can SHIP `.mcp.json` (user approves on first run) but cannot programmatically install servers.

Data-access-ladder consequence: rung 2 ("connector exists but not installed") is a web-lookup + user-approval flow, never automatic.

## 4. Hook events (2026 surface)

CLI shell-hook contract unchanged: JSON on stdin (`session_id`, `cwd`, `hook_event_name`, `tool_name`, `tool_input`, …), JSON on stdout (`continue`, `systemMessage`, `hookSpecificOutput.permissionDecision: allow|deny|ask|defer`, `updatedInput`). Exit 0 = parse stdout, 2 = blocking error, other = non-blocking.

Events the kernel already uses remain stable: SessionStart, SessionEnd, PreToolUse. Also available (CLI + SDK): PostToolUse, PostToolUseFailure, UserPromptSubmit, Stop, PermissionRequest, PermissionDenied, SubagentStart, SubagentStop, PreCompact, Setup.
TypeScript-SDK-only (NOT usable by Cairn's python command hooks): InstructionsLoaded, WorktreeCreate/Remove, CwdChanged, FileChanged, ConfigChange, TaskCreated/Completed, Notification, Elicitation, ElicitationResult, MessageDisplay, PostToolBatch, StopFailure, UserPromptExpansion, PostCompact.
Python SDK omits SessionStart/SessionEnd/StopFailure (irrelevant to Cairn's CLI command hooks, which do get SessionStart/End).

## 5. Plugin packaging limits

Plugins CAN ship: skills, agents, hooks (`hooks/hooks.json`), `.mcp.json`, `.lsp.json`, monitors, `bin/` executables, `settings.json` (only `agent`, `subagentStatusLine` keys), legacy `commands/`.
Plugins CANNOT ship: saved workflows (`.claude/workflows/*.js`) or CLAUDE.md.

**Vendoring consequence for the research engine:** deep-research/directing-research must be vendored as skills, with the workflow `.js` carried as a skill supporting file and launched via `Workflow({scriptPath: <plugin path>})`, and/or copied by the scaffolder into the instance's own `.claude/workflows/` for `/deep-research` availability inside instances.

Manifest: `.claude-plugin/plugin.json` requires `name` + `description`; omitted `version` → git SHA versioning. Local test: `claude --plugin-dir`. Plugin skills namespace as `/plugin:skill`.
