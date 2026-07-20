---
name: upgrade
description: Migrate a keel instance to the installed plugin version, never overwriting user-modified files
---

# /keel:upgrade

Run from inside a keel instance. Never silent, never destructive (P10: versioned releases only).

1. Read instance manifest keel_version and the version in
   ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json.
   Same → say so, stop. Instance newer → warn, stop.
2. Show the user the changelog between the two versions
   (${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md) BEFORE touching anything. Get a go-ahead.
3. Hook scripts are plugin-owned and never user-edited: copy every file from
   ${CLAUDE_PLUGIN_ROOT}/templates/hooks/ directly over the instance's .claude/hooks/
   (report each file replaced).
   Command files are managed-but-rendered: render each new
   ${CLAUDE_PLUGIN_ROOT}/templates/instance/commands/*.md by substituting
   {{keel_version}} (the NEW version) and {{intents}} (from manifest.json) into a temp dir.
   For each command file, check provenance first: if `git status --porcelain <file>` is empty
   AND `git log -1 --format=%s -- <file>` starts with "keel" (scaffold or a prior upgrade
   authored it, user never modified), replace it in place with the rendered new version and
   report "replaced". Otherwise run
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/upgrade/merge.py <rendered-new> <installed>` —
   merge.py rules: identical content → no-op; unmanaged (no managed-by-keel header) →
   untouched; managed but different → new version lands alongside as *.keel-new (a stale
   .keel-new from a skipped prior upgrade is replaced — latest wins), the user's file is
   never overwritten. CLAUDE.md and state/HOT.md are NOT upgraded — after scaffold they are
   user-owned living documents; their managed-by-keel header records provenance only.
4. List any *.keel-new files created and walk the user through each diff — they decide
   adopt/merge/ignore per file.
5. Update manifest keel_version. Run `python3 .claude/hooks/validate.py`. Commit:
   "keel upgrade <old> -> <new>".
