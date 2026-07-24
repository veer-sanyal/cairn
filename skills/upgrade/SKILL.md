---
name: upgrade
description: Migrate a cairn instance to the installed plugin version — plugin-owned hooks and research engine are always replaced; user-modified command files are never overwritten (.cairn-new)
---

# /cairn:upgrade

Run from inside a cairn instance. Never silent, never destructive (P10: versioned releases only).

1. Read instance manifest cairn_version and the version in
   ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json.
   Same → say so, stop. Instance newer → warn, stop.
1a. **Always check the source GitHub for a newer release first (network; degrade gracefully).**
   The installed plugin can itself be behind the upstream repo — upgrading an instance to a
   stale local copy is the trap this prevents. Read `homepage` from
   ${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json (e.g. `https://github.com/veer-sanyal/cairn`),
   derive `<owner>/<repo>`, and fetch the latest manifest version:
   `curl -fsSL https://raw.githubusercontent.com/<owner>/<repo>/main/.claude-plugin/plugin.json`
   (parse `version`). If GitHub's version is NEWER than the installed plugin version, STOP
   before touching the instance and give the user the exact three-step sequence — the plugin
   cannot update itself mid-run, because plugin code loads at session start, so this is
   necessarily manual and in this order:
     1. Update the plugin: `claude plugin update cairn@<marketplace>` (marketplace install),
        or `git pull` in the plugin's repo (local clone / local-path marketplace).
     2. **Restart Claude Code** — the newly-pulled code is inert until the next session start;
        upgrading now would still migrate the instance to the OLD installed version.
     3. Re-run `/cairn:upgrade` in this instance — it will then target the latest version.
   Say which install kind you detect if you can (marketplace vs clone); if unsure, show both
   commands. The user MAY still proceed to the currently-installed version instead — offer that
   as a deliberate choice, not the default. If the fetch fails (offline, rate-limited, no
   `curl`), note it in one line and continue with the local comparison — never block the
   upgrade on the network.
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
8. If the instance has no `origin` remote (`git remote` is empty), offer the same GitHub
   backup the builder does — ask once, default private, warn before public (see build Stage 5,
   "Offer to back the instance up on GitHub"). Skip silently if a remote already exists.
