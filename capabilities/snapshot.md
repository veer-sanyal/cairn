# Claude Code capabilities snapshot (for the Cairn builder)

Snapshot date: 2026-07-24 — refresh by re-verifying against official Claude Code docs before each release.

Changelog — 2026-07-24: re-verified for 0.8.x; MCP deferred tool-list cost 120 tokens per official context-window docs; no other changes.

This is the builder's *bundled* knowledge of the platform surface Cairn compiles onto. It is
deliberately thin — every token here is a distractor token at build time (P1). It documents
only what the kernel actually uses, exactly as the shipped `templates/hooks/*.py` use it. When
in doubt, the scripts are authoritative; this file summarizes them.

## Hooks

Configured per instance in `.claude/settings.json` (see `templates/instance/settings.json.tmpl`).
The plugin registers **zero** hooks of its own — all hooks are copied into the instance's
`.claude/hooks/` by the scaffolder, so they fire only inside that instance directory.

Each hook is a `command` hook: Claude Code runs `python3 <script>` with the event payload as a
**JSON object on stdin**, and reads the script's **stdout**. Kernel discipline (spec §1.3): a
hook exits 0 on every path; a deliberate block is expressed as JSON on stdout, not a nonzero
exit. Any internal error is swallowed (exit 0, no output = allow / no banner) so a crashed or
absent interpreter can never brick a session.

Events wired, and the stdin fields each script actually reads:

| Event | Matcher | Script | stdin fields read | stdout |
|---|---|---|---|---|
| `SessionStart` | — | `session_start.py` | `cwd`, `session_id` | banner JSON (below) |
| `SessionEnd` | — | `session_end.py` | `cwd`, `session_id`, `reason` | none (file write only) |
| `PreToolUse` | `Write\|Edit` | `guard_files.py` | `tool_name`, `tool_input.file_path`, `tool_input.content`, `cwd` | deny JSON or nothing |
| `PreToolUse` | `Bash` | `guard_bash.py` | `tool_name`, `tool_input.command`, `cwd` | deny JSON or nothing |

`cwd` is used to locate the instance root (walk up to a `manifest.json` carrying `cairn_version`);
if no root is found the hook exits silently — a hook outside a Cairn instance is a no-op.

### SessionStart I/O

Reads `cwd` + `session_id`. Side effects: appends a `session` start event (with a
`boot_context_est_tokens` estimate = resident bytes of `CLAUDE.md` + `state/HOT.md`, divided by
4) and may append a look-back `lapse` event. Emits a banner on stdout:

```json
{
  "hookSpecificOutput": { "hookEventName": "SessionStart", "additionalContext": "cairn boot: ..." },
  "systemMessage": "cairn boot: ..."
}
```

`additionalContext` is injected into the model's context; `systemMessage` is the user-visible
line where the platform surfaces it. Banner relay is best-effort by design (spec §1.2) — the
deterministic record is always the appended events, never the banner text.

### SessionEnd I/O

Reads `cwd`, `session_id`, `reason`. Appends a `session` end event with `duration_s` (computed
by matching the start event for this `session_id`) and `reason`. Writes no stdout — SessionEnd
cannot feed context. (The Stop hook fires after *every* turn, not at session end, and is
deliberately unused.)

### PreToolUse deny shape

A block is exit 0 plus this exact JSON on stdout; anything else (allow) is exit 0 with no output:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "<human-readable reason>"
  }
}
```

`guard_files.py` denies: any `Write`/`Edit` to `state/archive.jsonl` (append-only); a `Write`
that *overwrites* an existing `state/working/*` file unless the review sentinel
`.cairn/review-in-progress` exists (`Edit` is always allowed — P2 write-through); and a `Write`
whose `content` would exceed the file's hard size cap from `manifest.json` `caps`.
`guard_bash.py` heuristically denies destructive shell forms (`rm`, single-`>` truncation,
`truncate`/`shred`, `mv` of the archive) targeting `state/working`, `state/archive.jsonl`, or
`telemetry/events.jsonl`. `>>` append to the archive is allowed. The Bash matcher is explicitly
heuristic (spec §1.3); `/cairn:review` re-validation is the real backstop.

## Slash commands

Two kinds, both plain markdown:

- **Plugin commands** (`skills/*/SKILL.md` frontmatter `name:`) → `/cairn:build`, `/cairn:review`,
  `/cairn:upgrade`. These are the machinery; they live in the plugin, not the instance.
- **Instance commands** (`templates/instance/commands/*.md`, copied into `.claude/commands/`) →
  `/log`, `/suspend`, `/conclude`. Instance-local so they survive plugin uninstall (P13). Each
  is prose that instructs the model to run a `cairn_event.py` invocation via Bash to append a
  telemetry event. The builder selects the intent enum for `/log` from the closed trigger menu.

## Skills

The plugin's three capabilities ship as skills with YAML frontmatter (`name`, `description`) in
`skills/build/`, `skills/review/`, `skills/upgrade/`. They carry a deterministic helper each:
`build/scaffold.py` (generates an instance from a build-config JSON), `upgrade/merge.py`
(managed-file merge). Skills are prose protocols the model follows; the load-bearing determinism
lives in those two Python helpers, never in freeform generation.

## Subagents

Used as a fan-out/isolation primitive, not a scaffolded artifact (P3): the kernel prose
(`CLAUDE.md.tmpl`, review skill) instructs spawning a subagent for noisy reads — archive scans,
large searches — and returning only a condensed summary, to keep the main context budget lean.
No subagent definitions are shipped; this is a usage convention encoded in the instance's
`CLAUDE.md` and in `/cairn:review` Stage 2.

## MCP presence-detection

Cairn ships **no** MCP servers and requires none. The builder may note whatever MCP servers the
user already has connected and reference them when shaping an instance, but the kernel runtime
(hooks, telemetry, scaffolder) is pure `python3` stdlib and makes no MCP or network calls. MCP
presence is therefore advisory context for the interview only — never a runtime dependency.
