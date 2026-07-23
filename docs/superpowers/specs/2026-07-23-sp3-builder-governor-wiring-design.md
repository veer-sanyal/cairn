# SP3: Builder + Governor Wiring

**Status:** draft for user review
**Date:** 2026-07-23
**Parent:** umbrella spec §5 (census + ladder + blast radius), §6 (wiring), §7 (SP3 row). Doctrine references are P-refs into PRINCIPLES.md v2 (P16–P24 landed in SP2).

## Goal

Turn the level-zero doctrine into enforced behavior: the builder diagnoses and probes before scaffolding; the governor sweeps for expiry, capability drift, environment change, and metric corruption. Kernel code stays python3-stdlib and minimal — most wiring is skill doctrine, because the kernel's own P9/P23 logic says deterministic gates for what must always happen, model judgment for the rest.

## Design decisions (locked)

### 1. Failure-mode telemetry tags — zero kernel code
`cairn_event.py` already accepts arbitrary `key=val`; the tag set is doctrine, not schema. Six tags, adapted from P16's taxonomy (MAST 3 categories + the coding-agent misalignment forms) to personal-instance scale:
`failure_mode=spec` (did the wrong thing / misread intent) · `verify` (check missed a broken result, or none ran) · `context` (lost or stale state) · `overreach` (acted past the autonomy line) · `tooling` (data path or tool broke) · `upkeep` (system demanded too much — stays aligned with the existing lapse type).
`/log`'s friction path documents them; the governor reads frequencies. **De-automation rule (P16, P17):** same task class + same tag ≥3 times since the last review → the governor proposes moving that task below the autonomy line or adding a checked verifier — citing the events.

### 2. Environment census — manifest object, model-gathered, deterministically stored
New optional manifest field, written at build and refreshed at review:
```json
"census": {"date": "YYYY-MM-DD", "mcp_servers": ["..."], "surfaces": ["chrome", "computer-use"], "notes": "..."}
```
Only the live session can enumerate its tools (P23: servers enumerable, schemas not), so the *model* gathers (session tool list + `claude mcp list` via Bash where available) and the scaffolder/manifest stores. `validate.py` flags `census_stale` (soft) past 180 days — perishable class, P22 structural trigger.

### 3. Data-access ladder — recorded rungs with provenance
New optional manifest field:
```json
"data_paths": [{"need": "...", "rung": 1-5, "why": "...", "date": "YYYY-MM-DD"}]
```
Rungs per umbrella §5.2 (1 connected MCP/API · 2 installable connector, manual-assisted · 3 browser automation · 4 screenshot+vision · 5 manual entry). Builder records a rung + reason per data need; the governor's census diff proposes upgrades when a lower rung becomes available ("rung 1 appeared for chart data; instance is on rung 4").

### 4. Capability probes — pass^k at build time (P17)
Builder protocol for every load-bearing "the model can do X reliably" assumption: k=5 repeated trials on 2–3 sampled task instances via cheap subagents; all-pass = VERIFIED-probed, any-fail = redesign or de-automate (pass^k, not pass@k). Result recorded as a manifest `decisions[]` entry (existing lifecycle: grade, date, blast) — probes are decisions with evidence, not a new schema. Governor re-probes when the failure audit (§1) implicates the task class.

### 5. Governor sweeps — deterministic detection in validate.py, judgment in the review skill
`validate.py` (already run in review Stage 1, report-only, fail-soft) gains three soft checks:
- `research_expired` — any `Refresh-by: YYYY-MM-DD` line in `docs/RESEARCH.md` past today (P22: structural triggers, never model memory).
- `census_stale` — census.date older than 180 days (or absent when data_paths exist).
- `proxy_revalidation_due` — `manifest.metrics.last_revalidated` older than `cadence.proxy_revalidation_days` (default 365 — P22's hard annual ceiling; P18's Skalse consequence).
The review skill turns each finding into a Stage 4 proposal: re-research via `/cairn:research` (expiry), ladder upgrades (census diff), lever→north-star causal re-check against P18's four mechanisms (proxy revalidation, then stamp `last_revalidated`). Detection is deterministic; disposition stays human-gated BUILD/PARK/REJECT.

### 6. Ask-budget + blast-radius — manifest boundary object (P19)
```json
"boundary": {"ask_budget_per_session": 1, "autonomy": {"act": ["..."], "ask": ["..."], "never": ["..."]}}
```
Set in the build interview (blast-ordered, with recommended defaults — P19: asks are a rationed budget, frequency not depth drives abandonment). Review Stage 3 reports asks/session against the budget. Asks that ARE spent use inhibitive framing for one-way doors (existing blast-ordered ask machinery extends naturally). **v1 enforcement is instructional + telemetry-audited, not hook-enforced — an explicit [BET]** recorded in the spec and the scaffolded manifest's decisions[]; a PreToolUse autonomy gate is future work if telemetry shows overreach tags.

### 7. Scaffolder passthrough
`scaffold.py` accepts optional build-config fields `census`, `data_paths`, `boundary`; stamps `metrics.last_revalidated = created date` and `cadence.proxy_revalidation_days = 365`. All optional — old configs scaffold unchanged.

## Out of scope
- `/cairn:audit` (SP4).
- Hook-enforced autonomy gating (BET, above).
- doctrine/ dir migration (still SP1's RESEARCH.md decision).
- Instance upgrades for existing instances beyond normal hook-copy (new manifest fields are optional; upgrade skill needs no migration step).

## Testing
- `tests/test_validate_sweeps.py` — the three new checks: expired vs future Refresh-by, stale vs fresh vs absent census, revalidation due vs fresh vs absent (absent = legacy manifest → silent, fail-soft preserved).
- `tests/test_scaffold.py` — passthrough of census/data_paths/boundary; last_revalidated + proxy_revalidation_days stamped; omission still scaffolds clean.
- `tests/test_skills_exist.py` — new tokens: build ("census", "rung", "pass^k", "boundary", "ask_budget"), review ("research_expired", "census_stale", "proxy_revalidation", "failure_mode", "de-automat").
- log.md template: failure_mode tags documented (test_templates token check).

## Release
0.5.0. CHANGELOG "builder/governor wiring". validate.py/log.md changes reach existing instances via the normal `/cairn:upgrade` hook copy.
