---
name: upgrade
description: Migrate a cairn instance to the installed plugin version — plugin-owned hooks and research engine are always replaced; user-modified command files are never overwritten (.cairn-new)
---

# /cairn:upgrade

Run from inside a cairn instance. Never silent, never destructive (P10: versioned releases only).

1. Read instance manifest cairn_version and the version in
   ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json.
   Same → say so, stop. Instance newer → warn, stop.
2. Show the user the changelog between the two versions
   (${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md) BEFORE touching anything. Get a go-ahead.
3. Hook scripts are plugin-owned and never user-edited: copy every *.py file from
   ${CLAUDE_PLUGIN_ROOT}/templates/hooks/ directly over the instance's .claude/hooks/
   (report each file replaced).
   The research workflow is plugin-owned too: copy
   ${CLAUDE_PLUGIN_ROOT}/skills/research/deep-research.js over the instance's
   .claude/workflows/deep-research.js (create the directory if a pre-0.3.0 instance
   lacks it).
   Command files are managed-but-rendered: render each new
   ${CLAUDE_PLUGIN_ROOT}/templates/instance/commands/*.md by substituting
   {{cairn_version}} (the NEW version) and {{intents}} (manifest.json's intents list,
   rendered comma-joined: `plan, log, other`) into a temp dir.
   For each command file, check provenance first: if `git status --porcelain <file>` is empty
   AND `git log -1 --format=%s -- <file>` starts with "cairn" (scaffold or a prior upgrade
   authored it, user never modified), replace it in place with the rendered new version and
   report "replaced". Otherwise run
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/upgrade/merge.py <rendered-new> <installed>` —
   merge.py rules: identical content → no-op; unmanaged (no managed-by-cairn header) →
   untouched; managed but different → new version lands alongside as *.cairn-new (a stale
   .cairn-new from a skipped prior upgrade is replaced — latest wins), the user's file is
   never overwritten. CLAUDE.md and state/HOT.md are NOT upgraded — after scaffold they are
   user-owned living documents; their managed-by-cairn header records provenance only.
4. List any *.cairn-new files created and walk the user through each diff — they decide
   adopt/merge/ignore per file.
5. Update manifest cairn_version (do this before regenerating docs, next step, so they stamp
   the new version).
6. Regenerate the human-facing docs from the now-current manifest — they are generated
   artifacts, not user-authored, so this refreshes README.md + docs/MANUAL.md to the new
   version's templates and the instance's live metric contract:
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/build/render_docs.py manifest.json .`
   The renderer skips either doc the user has made their own (managed header removed) and
   reports it; a pre-this-feature instance simply gets them created.
7. Run `python3 .claude/hooks/validate.py`. Commit: "cairn upgrade <old> -> <new>".
