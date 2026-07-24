# Production-Readiness Pass Implementation Plan (0.8.1)

**Executed — shipped as 0.8.1**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Executed as four workstreams (A–D), each one implementer + review.

**Goal:** Close every finding from the six-dimension deep audit of 2026-07-24 (docs↔code consistency, runtime edge cases, skill-instruction integrity, open loops, research gaps, live e2e lifecycle) so v0.8.x is production-ready, not a prototype.

**Audit provenance:** 6 parallel auditors, 45 findings pre-dedup → 37 unique actions after merging cross-auditor duplicates (archive-writer, README-status, snapshot-refresh, P23-expiry each reported twice). Auditor reports are reproduced in the workstream sections' evidence lines.

**Branch:** `prod-readiness` off main (98c6c7b + docs commits). Ships as **0.8.1** (fixes only, no new capability).

**Locked decisions** (implementers do not re-litigate):
1. Sanctioned archive append is Bash `printf '%s\n' '<json>' >> state/archive.jsonl` — docs/deny-messages updated; no new cairn_event flag (YAGNI).
2. `/suspend` always logs `cause=suspended`, carrying the user's answer as `reason=<skipped|upkeep|other>`. `status_of` semantics unchanged (suspended = explicit pause).
3. `VERIFIED-probed` is NOT auto-adopt eligible (probes are perishable); canonical grade enum is VERIFIED / VERIFIED-probed / PREPRINT / THIN / BET.
4. Registry case-duplicate keys on case-insensitive filesystems: documented limitation (comment), no normalization code (POSIX normcase is identity; samefile scanning is over-engineering; prune + self-heal cover it).
5. guard_files Edit-growth gap: documented ceiling (`ponytail:` comment), no Edit size estimation.
6. Doctrine expiry becomes a repo test: any principle Verified > 12 months ago fails (P22 annual ceiling); perishable > 6 months fails. P23 and capabilities/snapshot.md are re-verified by a claude-code-guide agent in WS-C and re-dated.
7. Review Stage 3 asks-per-session: reworded to overreach-tag audit + conversational check (no new event type).
8. Research candidates (ranked by auditor 5) are RECORDED in the umbrella spec's gaps ledger, not executed in this pass: (1) drift/re-elicitation triggers [P14], (2) surrogate-index construction [P18], (3) cold-start handover [P24], (4) ask-budget dose-response [P19], (5) multi-instance patterns [SP6].

---

## Workstream A — Runtime hardening (code, TDD, one commit per numbered item where practical)

**Files:** templates/hooks/cairn_lib.py, session_start.py, session_end.py, guard_bash.py, guard_files.py, validate.py, skills/list/list_instances.py, tests/*

A1. **[CRITICAL] `read_text_safe` helper.** New in cairn_lib: `def read_text_safe(p): try: return Path(p).read_text(errors="replace") except OSError: return ""`. Use it in: cairn_lib.load_events, validate.py HOT.md read (~:95) and jsonl_integrity read (~:117), session_end.py events read (~:16), list_instances.py last_reconciled. Tests: non-UTF-8 byte (`b"\x80"`) in events.jsonl no longer suppresses validator findings (hard staleness finding still reported); binary HOT.md → findings survive; session_end still appends its end event with a binary byte in the log; a binary instance renders as a row in `--json` instead of killing the portfolio. (Runtime C1, I6, part of I3; the replaced-garbage line must surface as a jsonl_integrity finding, not vanish.)

A2. **[CRITICAL] Banner survives malformed manifest scalars.** session_start.py: guard the four reproduced shapes — `triggers[].days` as string (`pos_int(...) or default` at the gap_nudge/review_due compares), `metrics` as list (`isinstance` coerce at both read sites), `guardrails[]` entries that aren't dicts (skip), `guardrail.max` as string (coerce via try/float; skip on failure). Tests: each of the four manifests boots with a full banner (subprocess, assert "cairn boot:" present).

A3. **[IMPORTANT] Portfolio never dies on one bad entry.** list_instances.py: `reg_entry = reg_entry if isinstance(reg_entry, dict) else {}` at entry_for top; wrap per-entry construction so an exception on one path yields a `{"path": p, "status": "error", ...}` row instead of aborting. Sanitize name/purpose to strings (`str(x) if x is not None else ""`). Tests: null entry value, entry with name:null, one binary instance among healthy ones → full JSON array with the bad rows marked, healthy rows intact.

A4. **[IMPORTANT] append_event fail-soft; banner independent of the event write.** cairn_lib.append_event wraps its write in try/except OSError → returns None (telemetry is best-effort). session_start: the start-event write must not precede/gate banner assembly — wrap the call so a read-only/full disk still prints the banner. Test: chmod a-w telemetry dir → boot exits 0 WITH banner (restore perms in teardown; skip on root).

A5. **[IMPORTANT] guard_bash overwrite-verb parity.** Extend patterns: a protected path appearing as the write target of `cp`, `tee`, `dd of=`, `sort -o`, `install`, or `sed -i` is denied like `>` already is. Keep the docstring's honesty about heuristic coverage. Tests: each verb against state/archive.jsonl denied; `>>` append still allowed; the same verbs against ordinary files allowed.

A6. **[MINOR] guard_files resolves relative paths against the payload cwd/instance root** before relative_to (Runtime M9). Test: relative `state/archive.jsonl` Write payload → denied.

A7. **[MINOR] Same-second resume tie-break.** list_instances status_of: `parse_ts(e["ts"]) >= t` for the resumed check (a session start in the same second as the suspend counts as resumed). Adjust/extend test.

A8. **[MINOR] No untyped-lapse nag after a deliberate lapse.** session_start "worked" check: a `lapse` event with `deliberate == "true"` in the previous session's window counts as typed activity — no "cause unknown" line, no untyped lapse appended. Test: suspend-only session → next boot banner has no "cause unknown" and no new untyped lapse row. (E2E finding 2 — suspend.md's no-guilt promise.)

A9. **[MINOR] validate.py flags a top-level `"concluded"` key** in manifest.json (the conclude.md edit gone wrong — silently ignored by every reader today) as a soft finding `misplaced_concluded`. Test: manifest with top-level concluded → finding; correct placement → no finding. (Skills M7.)

A10. **[MINOR] Comments documenting accepted ceilings:** registry case-dup keys (cairn_lib registry_upsert), Edit-growth cap gap (guard_files). No behavior change.

## Workstream B — Skill & command integrity (markdown + two small code fixes, TDD for code)

**Files:** skills/build/SKILL.md, skills/review/SKILL.md, skills/research/SKILL.md, skills/list/SKILL.md, skills/upgrade/SKILL.md, templates/instance/commands/*.md, templates/instance/CLAUDE.md.tmpl, templates/hooks/guard_files.py, guard_bash.py, cairn_event.py, doctrine_write.py, skills/research/deep-research.js, tests/*

B1. **[CRITICAL] One true archive path.** Per locked decision 1: CLAUDE.md.tmpl:8 names the Bash `>>` append as the mechanism; guard_files.py:29 deny message says "append via Bash >> (e.g. printf '%s\n' '<json>' >> state/archive.jsonl); /log and cairn_event.py write telemetry, not the archive"; guard_bash.py:29 consistent; review SKILL Stage 2.5 shows the exact printf command for working→archive demotion. Test: deny-message text updated in guard tests.

B2. **[IMPORTANT] cairn_event.py cwd trap.** Code: fall back to `find_root(Path(__file__))` when `find_root(os.getcwd())` fails (the script lives in <instance>/.claude/hooks/, so its own path locates the instance). Test: invoke by absolute path from an outside cwd → event lands in the instance's events.jsonl. Docs: commands/*.md drop `$CLAUDE_PROJECT_DIR` (empty in Bash tool env — verified) in favor of the relative `.claude/hooks/cairn_event.py` invocation + one "run from the instance root" line; review SKILL already uses the relative form.

B3. **[IMPORTANT] /suspend event shape** (locked decision 2): suspend.md logs `lapse cause=suspended deliberate=true reason=<skipped|upkeep|other>`. list SKILL:22-23 wording matches. Test: none needed beyond existing status tests (shape documented, cairn_event accepts free key=val).

B4. **[IMPORTANT] Real trigger menu.** build SKILL Stage 4: the closed menu is exactly `gap_nudge, review_due, staleness_escalation, friction_accumulator, suspend_suggestion`; guardrail regression is a manifest.metrics.guardrails behavior and intents are a manifest field — not triggers. Remove the three phantom entries.

B5. **[IMPORTANT] Canonical grade enum + auto-adopt ruling** (locked decision 3): build Stage 5 states the enum; review SKILL references it identically; explicit line: VERIFIED-probed never auto-adopts.

B6. **[IMPORTANT] Research persistence ordering.** build Stage 2.5: results are held as saved result.json files during the interview; Stage 5 reads "after scaffold.py succeeds, run doctrine_write.py against the new instance root for each saved result.json — never hand-write RESEARCH.md, never run doctrine_write before scaffold."

B7. **[IMPORTANT] doctrine_write accepts refuted-only runs.** Code: a run with empty findings/confirmed but non-empty refuted writes the refuted block (do-not-build-on negatives are the point). Test: refuted-only result.json → RESEARCH.md gains the refuted entries; truly-empty run still refuses.

B8. **[IMPORTANT] Degraded-mode result.json example.** research SKILL: 6-line example with findings[].confidence mapping note (high→VERIFIED, medium/low→THIN; "cap at THIN" = set confidence medium).

B9. **[IMPORTANT] Review Stage 3 computability.** Asks-per-session → overreach-tag audit + conversational check (locked decision 7). Lapse report includes `untyped` alongside the four typed causes. Standing guardrail names: build Stage 3 and review Stage 4 both say `boot_context_bytes` + upkeep-burden (measured via lapse cause=upkeep events) — one vocabulary.

B10. **[MINOR] Reference hygiene:** spec citations get real paths (build SKILL "spec §2.1" → docs/superpowers/specs/2026-07-19-cairn-design.md §2.1; list_instances.py + doctrine_write.py docstrings name their spec files); upgrade SKILL "every *.py file" + `{{intents}}` renders comma-joined; deep-research.js error text uses the scriptPath call shape; build SKILL documents the manual session_start invocation (`echo '{"cwd":"'$PWD'"}' | python3 .claude/hooks/session_start.py`).

## Workstream C — Doctrine self-compliance (research auditor's disease: the doctrine exempts itself)

**Files:** docs/PRINCIPLES.md, docs/research/research-mechanisms-claude-code-2026-07.md, capabilities/snapshot.md, skills/build/SKILL.md, skills/review/SKILL.md, templates/instance/commands/log.md, tests/test_principles.py, docs/superpowers/specs/2026-07-23-level-zero-umbrella-design.md

C1. **[CRITICAL] Doctrine expiry is enforced by the repo, honestly described.** PRINCIPLES.md:10 and :372 rewritten: the governor's sweep reads instance RESEARCH.md; THIS file is swept by the repo's own test suite. tests/test_principles.py gains age checks per locked decision 6 (Verified: YYYY-MM parsed; >12 months any → fail; >6 months perishable → fail). The test must pass at HEAD after C2 re-dates P23.

C2. **[CRITICAL] P23 + snapshot refresh.** A claude-code-guide agent re-verifies the mechanisms doc's claims and capabilities/snapshot.md against current official docs; both get re-dated (2026-07-24) with a changelog line for anything that changed; PRINCIPLES P23's Verified stamp updates. build SKILL Stage 1.5 references capabilities/snapshot.md explicitly (closing its orphaning).

C3. **[IMPORTANT] BET settling loops wired.** P14: review SKILL Stage 3 gains a goal-drift check (typed-lapse pattern or input-metric decline over 2 review periods → re-run the artifact-based goal interview; log `re_elicit outcome=<changed|unchanged>` — cairn_event takes any TYPE, no code). P24: review SKILL states the handover rule (after the first completed review, instance telemetry cites outrank generic doctrine P-refs where they conflict — auto-adopt evidence line updated to match); P24's text points at the `re_elicit`/proposal telemetry as its settling evidence. P18: PRINCIPLES P18 BET paragraph names its watch condition (surrogate-index literature — recorded as research candidate #2).

C4. **[IMPORTANT] Cross-labels and small doctrine honesty fixes.** P12 + build Stage 3: one sentence noting the leading-indicator *construction* method is BET-grade (P18). P19: build Stage 3 gains the over-constraint check (an autonomy table that is all ask/never gets pushed back on once). P23 legacy-commands deviation recorded (instance commands are parameter-rendered per instance; kernel-release exception noted in the mechanisms doc). P22-vs-research-skill: doctrine_write refuses `durable` class unless the run's decision names why it can't rot (one guard + one skill line) — or if that's heavy, the review sweep flags durable-classed entries in RESEARCH.md for manual confirmation; implementer picks the smaller diff.

C5. **[MINOR] Gaps ledger updated.** Umbrella spec's ledger gains: the 5 ranked research candidates (locked decision 8), the P5 probe-tagging idea, and the open-bets row note about the README any-domain framing (domain generality, not niche claims).

## Workstream D — Docs truth (README/CHANGELOG/specs/map/plans)

**Files:** README.md, CHANGELOG.md, templates/instance/SYSTEM-MAP.md.tmpl, docs/superpowers/specs/2026-07-23-sp6-cross-instance-registry-design.md, docs/superpowers/plans/*.md, tests/test_session_start.py

D1. **[IMPORTANT] README Status → v0.8.1**, 142+ tests (use the count after WS-A/B land), SP6 added to the chain.
D2. **[IMPORTANT] Registry privacy lines include purpose:** README bullet, CHANGELOG 0.8.0 entry, list SKILL header, SP6 spec §1/§7 self-consistency — "names, paths, timestamps, and your one-line purpose (user-authored text); never metrics or state."
D3. **[IMPORTANT] SYSTEM-MAP template flows match the kernel:** session-start flow gains the registry-upsert node and `~/.cairn/registry.json` in Writes; suspend-conclude flow's Writes gains manifest.json.
D4. **[IMPORTANT] Upgrade overwrite claim scoped:** README + upgrade SKILL frontmatter: hooks and the research engine are plugin-owned and always replaced; the never-overwrite guarantee is for command files (.cairn-new).
D5. **[IMPORTANT] Single-machine limitation documented** (README "What Cairn executes on your machine" + instance CLAUDE.md.tmpl one line): one machine, one session at a time; multi-machine git sync unsupported in v1.
D6. **[MINOR] SP6 spec amendments:** silent coercion is shipped behavior (no warning line); list column is last_reconciled (no separate staleness flag); plan's "~17 new" → 21.
D7. **[MINOR] README wording:** "a broken script warns" → "a broken script goes silent — it never bricks a session (hooks are fail-soft; failures surface at the next review)"; file tree gains `.cairn/ # review sentinel`.
D8. **[MINOR] Plans stamped:** all 7 plan headers gain "**Executed — shipped as <version> (<commit>)**"; stale "defined in step 2" comment removed from tests/test_session_start.py:3.

## Verification (final gate)

1. Full suite green (expect ~155+ after new tests).
2. Re-run the e2e lifecycle walk (scaffold→boot→guards→suspend→conclude→list→move→prune) in a sandbox — all steps PASS including the two fixed e2e findings.
3. Re-run a docs-consistency spot-check on every WS-D claim.
4. Doctrine expiry test passes with re-dated P23.
5. Merge `prod-readiness` → main as 0.8.1 with CHANGELOG entry; push; suite green on main.
