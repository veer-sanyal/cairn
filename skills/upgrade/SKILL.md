---
name: upgrade
description: Migrate a keel instance to the installed plugin version, never overwriting user-modified files
---

# /keel:upgrade

Run from inside a keel instance. Never silent, never destructive (P10: versioned releases only).

1. Read instance manifest keel_version and the plugin's .claude-plugin/plugin.json version.
   Same → say so, stop. Instance newer → warn, stop.
2. Show the user the changelog between the two versions (CHANGELOG.md in the plugin) BEFORE
   touching anything. Get a go-ahead.
3. For every file in the plugin's templates/hooks/ and templates/instance/commands/, run:
       python3 <plugin>/skills/upgrade/merge.py <new-file> <instance-installed-path> --original <old-template-path-if-available>
   merge.py rules: unmanaged file → untouched; managed-by-keel + unmodified → replaced;
   managed-by-keel + user-modified → new version lands alongside as *.keel-new, user's file
   untouched. Report every action taken.
4. List any *.keel-new files created and walk the user through each diff — they decide
   adopt/merge/ignore per file.
5. Update manifest keel_version. Run `python3 .claude/hooks/validate.py`. Commit:
   "keel upgrade <old> -> <new>".
