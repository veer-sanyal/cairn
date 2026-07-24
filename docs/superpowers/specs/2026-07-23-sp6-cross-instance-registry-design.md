# SP6: Cross-Instance Registry — Discovery, Routing, Read-Only Peeks

**Status:** draft for user review
**Date:** 2026-07-23
**Origin:** user request post-SP5: with multiple instances there is no way to see them all ("show me my systems and their health"), resolve one by name from outside its directory, or ask one system about another. Today the binding is purely cwd — an instance's identity is the directory you launched in, and Cairn has zero awareness that other instances exist.

## Goal

A lightweight global index at `~/.cairn/registry.json` that instances maintain themselves, plus one new plugin skill (`/cairn:list`) that renders a portfolio view, resolves instance names to paths (routing), and supports read-only cross-instance peeks via condensed-return subagents. Isolation and single-writer discipline are preserved: the registry holds pointers, never state; nothing ever writes across an instance boundary.

## Design decisions (locked)

1. **The registry is a rebuildable cache, never a source of truth.** Schema-versioned JSON keyed by canonical instance path (paths are unique; names may collide and are disambiguated by path at display time):

```json
{
  "version": 1,
  "instances": {
    "/abs/path/to/instance": {
      "name": "job-search",
      "purpose": "Land a staff PM role by December",
      "created": "2026-07-23",
      "last_session": "2026-07-23T22:41:09Z",
      "cairn_version": "0.8.0"
    }
  }
}
```

   Pointers and timestamps only — no metrics, no state, no content. Everything durable already lives in each instance's `manifest.json`; the registry indexes it. Consequences: losing or deleting the registry loses nothing (instances re-register on next boot); a corrupt registry is quarantined to `registry.json.bad` with a warning and rebuilt from subsequent boots. (P4 index-first: hold identifiers, load content just-in-time.)

2. **Two writers, both scripts that already run.**
   - `scaffold.py` upserts an entry after a successful scaffold. Registry write failure warns and never fails the build.
   - `session_start.py` upserts on every boot: refreshes `last_session` and re-reads name/purpose/`cairn_version` from the manifest — so renames, kernel upgrades, and moved directories self-heal on the next open.

   (`/cairn:list` also writes through the same helper, but only on an explicit user confirmation — registering an unregistered instance, §3, or pruning a missing entry, §4. The two *automatic* writers above are the only unprompted ones.)

   The upsert helper lives in `cairn_lib.py` (already shared plugin↔instance, already copied into instances). Writes are atomic: temp file + `os.replace`, so concurrent boots cannot corrupt the file. Fail-soft like every cairn hook — a broken registry never bricks a session. `~/.cairn/` location honors `$CAIRN_HOME` if set (test isolation; no other consumers).

3. **Existing instances register on their next upgrade or by explicit offer — no silent scan.** Pre-SP6 instances carry the old `session_start.py`; they join the registry after `/cairn:upgrade`, or when `/cairn:list` is run inside an unregistered instance and offers "register this instance?" (user confirms). The plugin never walks the filesystem looking for instances.

4. **`/cairn:list` — the portfolio view (new plugin skill).** Reads the registry, then reads *live* per entry from the instance's own files: status from the `telemetry/events.jsonl` tail (last suspend/conclude/session event → active | suspended | concluded), `Last reconciled` stamp from `state/HOT.md`, north-star name from `manifest.json`. Renders one table: name · purpose · status · last session · staleness flag. A path that no longer resolves to a manifest shows as `missing — moved or deleted?` and is removed only on user confirmation (the user is the gate; no auto-pruning). P13 constraint: the list reports status, never guilt — no "you've neglected X for N days" framing, ever.

5. **Routing is resolution, not teleportation.** The skill resolves a spoken name/purpose against the registry (substring/fuzzy on `name` and `purpose`; ambiguity → show candidates, user picks) and hands over the path, optionally with a peek. It never pretends to work inside another instance from outside: hooks, banner, and telemetry exist only in a session opened in that directory, and simulating them would silently drop every invariant. Full work = open a session there.

6. **Peeks are P3 condensed-return fan-out across a directory boundary.** From inside instance A, a question about instance B resolves B via the registry and spawns a read-only subagent that reads B's `state/HOT.md` + `manifest.json` (nothing else by default) and returns a condensed summary (~1–2K tokens) to A's session. B's files never enter A's main context; nothing ever writes into B (single-writer, P20). v1 enforcement is instructional + telemetry-audited — an `overreach` failure-mode tag on violation — recorded as a BET-grade decision (same precedent as the boundary contract) so the governor revisits if overreach events appear.

7. **README privacy amendment.** "What Cairn executes on your machine" gains one line: one global metadata file, `~/.cairn/registry.json` — names, paths, timestamps only; `cat` it any time; delete it and instances re-register on next boot. The zero-global-hooks claim is unchanged and stays true.

## Out of scope (recorded, not rejected)

- **Meta-review across instances** — a governor-style pass over all systems (shared patterns, conflicting commitments, decay). The Option C "hub instance" growth path; design it only when someone runs enough instances to want it.
- **Events/handoffs** — one instance writing tasks/state into another. Breaks single-writer; requires its own boundary design.
- **Shared-facts store** — a common read-only store (timezone, weekly hours). Revisit if peek telemetry shows repeated identical lookups.
- **Hook-enforced peek read-only-ness** — v1 is instructional + audited (decision graded BET); a `guard_files` deny on writes outside the instance root is the obvious v2 if overreach appears.

## Testing

pytest, same suite conventions as the existing 92 tests:

- **registry lib (`cairn_lib.py`):** upsert creates file + parent dir; upsert updates existing entry without touching others; atomic write (temp + replace); corrupt JSON → quarantined to `.bad`, fresh registry written, warning emitted; non-object JSON handled (`{}` fallback, consistent with `manifest()`); `$CAIRN_HOME` override respected.
- **scaffold integration:** successful scaffold registers the instance; registry write failure (unwritable dir) warns but scaffold succeeds.
- **session_start integration:** boot upserts `last_session`; a moved instance (old path stale, new path booted) yields both entries with the old one failing the existence check at list time; manifest rename reflected on next boot.
- **list behavior:** fake registry with one live, one missing, one concluded instance → correct table states; missing entry removed only on confirmation path.
