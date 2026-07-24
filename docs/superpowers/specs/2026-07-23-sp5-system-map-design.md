# SP5: SYSTEM-MAP.md — One Source of Truth for What the System Does

**Status:** draft for user review
**Date:** 2026-07-23
**Origin:** user request post-SP4: every instance (and every audited system) carries a canonical flowchart document of every workflow, so failure analysis has a design to point at and the system's behavior isn't hidden across prompts and hooks.

## Goal

A single, consistently-named document — `docs/SYSTEM-MAP.md` — in every Cairn instance and every audited system: one Mermaid flowchart per workflow plus machine-checkable metadata, created at build, reconstructed-or-reused at audit, kept current by the governor, staleness-checked by the validator.

## Design decisions (locked)

1. **Format: Mermaid + metadata convention, one file.** Mermaid because it is text-native (model-parseable), GitHub-rendered, and git-diffable. Pure diagrams aren't machine-checkable, so each flow section follows this exact shape:

```markdown
## Flow: <stable-id> — <title>
Trigger: <what starts it> · Writes: <files/none> · Verification: <what checks it/none> · Boundary: act|ask|never

​```mermaid
flowchart TD
  ...
​```
```

   File header carries `Last reconciled: YYYY-MM-DD` (same STAMP convention as HOT.md). Flow ids are stable slugs (`session-start`, `log-event`, `review-cycle`, ...) — telemetry may cite them (`flow=<id>` rides cairn_event's free-form key=val; zero kernel change) and the governor's failure audit correlates tags to flows when cited. P16 linkage: the map is where "failures are design flaws" gets a design to point at — the Verification field being "none" on a flow that writes files is a finding in itself.

2. **Born at build.** `templates/instance/SYSTEM-MAP.md.tmpl` ships the seven kernel flows pre-authored (session-start, session-end, log-event, guard-write, review-cycle, suspend/conclude, upgrade) with `{{instance_name}}`/`{{today}}` substitutions; scaffold.py renders it to `docs/SYSTEM-MAP.md`. The build skill's final stage instructs the builder to APPEND instance-specific flows (triggers it configured, working-file update paths, any agentic runs it designed) before the initial commit — the kernel flows are template-guaranteed, the instance flows are authored while the design is freshest.

3. **Checked-or-created at audit.** Audit Stage 0 gains the map-first rule: if `docs/SYSTEM-MAP.md` exists, read it and *drift-check* it against reality (flows that reference removed skills/hooks, mechanisms present in the repo but absent from the map — drift is a finding); if absent, reconstructing every workflow into a new SYSTEM-MAP.md is the FIRST deliverable of the audit, before the doctrine walk — the walk then cites flow ids.

4. **Kept current by the governor.** Review Stage 4: any applied BUILD that changes a flow updates the map section and the stamp in the same application step (a design change without a map update is an incomplete BUILD). Validator soft-checks (`system_map`): only when the file EXISTS — stamp missing or older than `2 × cadence.review_days` → soft staleness finding. A missing map is deliberately silent in the validator (legacy instances must not be mechanically nagged); the review skill instead proposes creating it once, at the next review. Fail-soft, report-only, same as every sweep.

5. **Boot cost: zero.** The map lives in docs/, loaded on demand only (P1). CLAUDE.md.tmpl's owner map gains one pointer line ("how the system works → docs/SYSTEM-MAP.md") so sessions can find it.

## Out of scope
- Rendering/preview tooling (GitHub renders Mermaid; that's enough).
- Mechanical mermaid-syntax validation in the kernel (report-only stamp/existence checks only; syntax errors are visible the moment the file is viewed).
- Auto-generation of flows from code analysis (the model authors flows; the validator checks freshness, not truth — truth is the governor's drift-check job).

## Testing
- `tests/test_templates.py`: SYSTEM-MAP.md.tmpl exists, has stamp line + all seven kernel flow ids + no unrendered placeholder risk.
- `tests/test_scaffold.py`: scaffolded instance has `docs/SYSTEM-MAP.md` rendered (no `{{`), stamp = today.
- `tests/test_validate_sweeps.py`: system_map missing → soft finding; present+fresh → silent; stale stamp → soft finding.
- `tests/test_skills_exist.py`: build tokens += ["SYSTEM-MAP"], review += ["SYSTEM-MAP"], audit += ["SYSTEM-MAP", "drift"].

## Release
0.7.0 on top of SP4's 0.6.0 (same branch line). Upgrade skill: SYSTEM-MAP.md.tmpl is instance-authored after scaffold (like HOT.md) — upgrade never overwrites it; pre-0.7.0 instances get the map via a governor proposal, not the upgrade.
