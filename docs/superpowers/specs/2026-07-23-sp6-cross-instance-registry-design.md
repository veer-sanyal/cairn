# SP6: Cross-Instance Registry — Discovery, Routing, Read-Only Peeks

**Status:** reviewed (fresh-context subagent, 8 findings incorporated) — approved for planning
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
      "last_session": "2026-07-23T22:41:09+00:00",
      "cairn_version": "0.8.0"
    }
  }
}
```

   Pointers and timestamps only — no metrics, no state, no content. `last_session` uses `cairn_lib.now_iso()` (isoformat, `+00:00` offset) — one timestamp format across the codebase, same as every event. Everything durable already lives in each instance's `manifest.json`; the registry indexes it. Consequences: losing or deleting the registry loses nothing (instances re-register on next boot); a corrupt or non-object registry is overwritten with a fresh `{"version": 1, "instances": {}}` plus one warning line — the same coerce-don't-crash behavior `manifest()` already models. No quarantine file: if the registry's loss costs nothing, preserving its corpse buys nothing. (P4 index-first: hold identifiers, load content just-in-time.)

2. **Manifest gains `purpose`.** `one_line_purpose` currently lands only in the rendered `CLAUDE.md`, not in `manifest.json` — so the registry could not read it. scaffold.py adds `"purpose"` to the manifest's `instance` object. The upsert helper falls back to `""` when the field is absent (pre-SP6 manifests). `tests/conftest.py`'s MANIFEST fixture gains the field.

3. **Two automatic writers, both scripts that already run.**
   - `scaffold.py` upserts an entry after a successful scaffold. scaffold's stated contract is "hard failures are correct here" — the registry write is the one deliberate exception: wrapped in its own try/except, warns to stderr, never fails the build (the instance is fine; it will self-register on first boot).
   - `session_start.py` upserts on every boot: refreshes `last_session` and re-reads name/purpose/`cairn_version` from the manifest — so renames, kernel upgrades, and moved directories self-heal on the next open. **Placement:** the upsert runs *before* the concluded-instance early return (concluded instances still refresh `last_session` and self-heal paths), and is wrapped in its own try/except — it must never reach the outer catch-all, which would eat the entire boot banner.

   (`/cairn:list` also writes through the same helper, but only on an explicit user confirmation — registering an unregistered instance, §5, or pruning a missing entry, §6. The two automatic writers above are the only unprompted ones.)

   The upsert helper lives in `cairn_lib.py`. Instances get it by copy, as today. Plugin-side, scaffold.py imports it via `sys.path.insert` on `templates/hooks/` (the exact mechanism the test suite already uses); note cairn_lib is *copied* into instances today, not imported by any plugin script — this is the first plugin-side import, and it is one line. Writes are atomic: temp file + `os.replace`, so concurrent boots cannot corrupt the file. Registry location is `~/.cairn/`, honoring `$CAIRN_HOME` if set. No env-var collision: no hook reads any env var today.

4. **Test isolation is mandatory, not registry-test-local.** Every existing hook test runs scripts as subprocesses inheriting the real environment — an unconditional boot upsert would pollute the developer's real `~/.cairn/` from the whole suite. conftest's `run_script` sets `CAIRN_HOME=<tmp>` for **every** invocation, not just registry tests. This is the primary justification for `$CAIRN_HOME` existing.

5. **Existing instances register on their next upgrade or by explicit offer — no silent scan.** Pre-SP6 instances carry the old `session_start.py`; they join the registry after `/cairn:upgrade` (which copies `templates/hooks/` wholesale — that path already delivers this), or when `/cairn:list` is run inside an unregistered instance and offers "register this instance?" (user confirms). The plugin never walks the filesystem looking for instances.

6. **`/cairn:list` — the portfolio view (new plugin skill).** Reads the registry, then reads *live* per entry from the instance's own files. Status derivation (in precedence order):
   - **concluded** ← `manifest.instance.concluded` is true (the authoritative flag `/conclude` already sets; the kernel already honors it at boot). Never derived from the event tail.
   - **suspended** ← last `lapse` event with `deliberate == "true"` and `cause == "suspended"` in `telemetry/events.jsonl`, with no `session phase=start` event after it. (Values are strings — `cairn_event.py` stores all values as strings. `cause=skipped` does **not** count: a deliberate skip is a lapse type, not a suspension.)
   - **active** ← otherwise.

   A naive "last event" read is wrong by construction — `session_end.py` appends a `session phase=end` event after any suspend/conclude in the same session, so the tail is always a session event. Plus per entry: `Last reconciled` stamp from `state/HOT.md`, north-star name from `manifest.json`. Renders one table: name · purpose · status · last session · staleness flag. A path that no longer resolves to a manifest shows as `missing — moved or deleted?` and is removed only on user confirmation (the user is the gate; no auto-pruning). P13 constraint: the list reports status, never guilt — no "you've neglected X for N days" framing, ever.

7. **Routing is resolution, not teleportation.** The skill resolves a spoken name/purpose against the registry (substring/fuzzy on `name` and `purpose`; ambiguity → show candidates, user picks) and hands over the path, optionally with a peek. It never pretends to work inside another instance from outside: hooks, banner, and telemetry exist only in a session opened in that directory, and simulating them would silently drop every invariant. Full work = open a session there.

8. **Peeks are P3 condensed-return fan-out across a directory boundary.** From inside instance A, a question about instance B resolves B via the registry and spawns a read-only subagent that reads B's `state/HOT.md` + `manifest.json` (nothing else by default) and returns a condensed summary (~1–2K tokens) to A's session. B's files never enter A's main context; nothing ever writes into B (single-writer, P20). v1 enforcement is instructional + telemetry-audited — an `overreach` failure-mode tag on violation — recorded as a BET-grade decision (same precedent as the boundary contract) so the governor revisits if overreach events appear.

9. **README privacy amendment.** "What Cairn executes on your machine" gains one line: one global metadata file, `~/.cairn/registry.json` — names, paths, timestamps only; `cat` it any time; delete it and instances re-register on next boot. The zero-global-hooks claim is unchanged and stays true.

## Out of scope (recorded, not rejected)

- **Meta-review across instances** — a governor-style pass over all systems (shared patterns, conflicting commitments, decay). The "hub instance" growth path; design it only when someone runs enough instances to want it.
- **Events/handoffs** — one instance writing tasks/state into another. Breaks single-writer; requires its own boundary design.
- **Shared-facts store** — a common read-only store (timezone, weekly hours). Revisit if peek telemetry shows repeated identical lookups.
- **Hook-enforced peek read-only-ness** — v1 is instructional + audited (decision graded BET); a `guard_files` deny on writes outside the instance root is the obvious v2 if overreach appears.

## Testing

pytest, same conventions as the existing suite (121 tests at time of writing):

- **conftest:** `run_script` exports `CAIRN_HOME=<tmp>` on every subprocess invocation (§4) — no existing test may touch the real `~/.cairn/`.
- **registry lib (`cairn_lib.py`):** upsert creates file + parent dir; upsert updates existing entry without touching others; atomic write (temp + replace); corrupt/non-object JSON → fresh registry written with warning (no crash, no quarantine); `$CAIRN_HOME` override respected; `purpose` fallback to `""` on pre-SP6 manifests.
- **scaffold integration:** successful scaffold registers the instance (manifest now carries `purpose`); registry write failure (unwritable `CAIRN_HOME`) warns but scaffold succeeds.
- **session_start integration:** boot upserts `last_session`; upsert failure (unwritable registry) still prints the full banner; concluded instance still refreshes `last_session`; a moved instance (old path stale, new path booted) yields both entries with the old one failing the existence check at list time; manifest rename reflected on next boot.
- **status derivation:** concluded via manifest flag beats any event tail; suspend event with a later `session phase=start` → active; suspend event with only a later `session phase=end` (same session) → still suspended; `cause=skipped` → active.
- **list behavior:** fake registry with one live, one missing, one concluded instance → correct table states; missing entry removed only on confirmation path.

## Release

Ships as **0.8.0** (new capability, new manifest field, new skill). Upgrade path: `/cairn:upgrade` copies the new hooks wholesale, which is exactly what delivers self-registration to existing instances — no migration step. CHANGELOG entry covers the manifest `purpose` addition and the new global file with its privacy note.
