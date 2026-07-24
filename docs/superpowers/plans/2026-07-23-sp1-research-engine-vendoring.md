# SP1: Research Engine Vendoring Implementation Plan

**Executed — shipped as 0.3.0 (4a772b0)**

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vendor the directing-research + deep-research engine into Cairn as `skills/research/`, so every builder/governor research run uses the plugin's own claim-scaled, 3-vote adversarial engine — no dependency on the user's global setup.

**Architecture:** The workflow script ships as a skill supporting file (plugins cannot ship saved workflows — verified against docs, see `docs/research/research-mechanisms-claude-code-2026-07.md` §5) and is launched via `Workflow({scriptPath: ...})`. The scaffolder also copies it into each instance's `.claude/workflows/` so instances get `/deep-research` natively. A new stdlib helper `doctrine_write.py` (shipped with the kernel hooks) deterministically converts an engine result JSON into graded, dated, refresh-by-stamped sections of the instance's `docs/RESEARCH.md`. The `/cairn:research` skill is the mandatory front door: frame the decision (directing-research discipline), launch, persist.

**Tech Stack:** python3 stdlib only (repo invariant), plain-JS workflow script (self-contained, no imports), pytest.

**Two deliberate deviations from the umbrella spec, to flag at review:**
1. Engine output persists to `docs/RESEARCH.md` (the existing instance convention the governor already reads), NOT a new `doctrine/` dir. Migration, if ever, is SP3's call. Smallest diff; no broken references.
2. Instance findings use the existing instance grade vocabulary (VERIFIED / THIN / BET from build Stage 2.5), not PRINCIPLES.md's [VERIFIED]/[PREPRINT]. Mapping: engine confidence `high`→VERIFIED, `medium`/`low`→THIN, refuted→"Refuted — do not build on" section.

**Source material:** the user's `~/.claude/workflows/deep-research.js` (427 lines, self-contained — vendored verbatim) and `~/.claude/skills/directing-research/SKILL.md` (discipline condensed into the new skill; not copied verbatim because Cairn's front door must also cover persistence and degraded mode).

---

### Task 1: Vendor the workflow script

**Files:**
- Create: `skills/research/deep-research.js` (verbatim copy)
- Test: `tests/test_research_engine.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_research_engine.py`:

```python
from conftest import REPO

WF = REPO / "skills" / "research" / "deep-research.js"

def test_vendored_workflow_exists_and_is_intact():
    text = WF.read_text()
    # load-bearing invariants of the engine, not cosmetic strings:
    assert "export const meta" in text
    assert "name: 'deep-research'" in text
    assert "const VOTES_PER_CLAIM = 3" in text          # 3-vote adversarial
    assert "const REFUTATIONS_REQUIRED = 2" in text
    assert "VERIFY_FLOOR_PER_ANGLE" in text             # claim-scaled, per-angle floors
    assert "synthesisDegraded" in text                  # verified layer survives synth failure
    assert "GROUNDING" in text                          # honors directing-research grounding
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_research_engine.py -v`
Expected: FAIL (FileNotFoundError — `skills/research/deep-research.js` does not exist)

- [ ] **Step 3: Copy the script verbatim**

```bash
mkdir -p skills/research
cp ~/.claude/workflows/deep-research.js skills/research/deep-research.js
```

Do NOT edit the file. It is self-contained (no imports, no fs, no Date.now) and already implements claim-scaled sizing and model tiering. Divergence from the user's personal copy is expected and fine from here on — this is a vendored fork.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_research_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/research/deep-research.js tests/test_research_engine.py
git commit -m "feat(sp1): vendor deep-research workflow script as skill supporting file"
```

---

### Task 2: `doctrine_write.py` — deterministic engine-result → RESEARCH.md persister

**Files:**
- Create: `templates/hooks/doctrine_write.py` (rides the existing scaffold hook-copy loop AND the upgrade skill's wholesale hooks copy — zero new copy logic; it is a kernel utility, not an event hook, like `validate.py`)
- Test: `tests/test_doctrine_write.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_doctrine_write.py`:

```python
import json
from conftest import run_script

RESULT = {
    "question": "Q", "synthesisDegraded": False,
    "summary": "s",
    "findings": [
        {"claim": "Spacing beats massing", "confidence": "high",
         "sources": ["https://a.example/p1", "https://b.example/p2"],
         "evidence": "meta-analysis", "vote": "3-0"},
        {"claim": "20min sessions optimal", "confidence": "medium",
         "sources": ["https://c.example/blog"], "evidence": "one study", "vote": "2-1"},
    ],
    "refuted": [{"claim": "Learning styles matter", "vote": "0-3", "source": "https://d.example"}],
    "caveats": "small samples",
}

def write(root, result, argv_extra=()):
    rj = root / "result.json"
    rj.write_text(json.dumps(result))
    return run_script("doctrine_write.py",
                      argv=[str(rj), str(root), "--domain", "study cadence", *argv_extra])

def test_writes_graded_sections(instance):
    r = write(instance, RESULT)
    assert r.returncode == 0, r.stderr
    text = (instance / "docs" / "RESEARCH.md").read_text()
    assert "## study cadence — researched" in text
    assert "**VERIFIED** Spacing beats massing" in text
    assert "**THIN** 20min sessions optimal" in text          # medium → THIN
    assert "Refuted — do not build on" in text
    assert "Learning styles matter" in text
    assert "small samples" in text
    assert "https://a.example/p1" in text

def test_perishability_sets_refresh_by(instance):
    r = write(instance, RESULT, ("--perishability", "durable"))
    assert r.returncode == 0, r.stderr
    text = (instance / "docs" / "RESEARCH.md").read_text()
    assert "Refresh-by: on contradiction" in text
    # default class is semi-durable → a dated refresh line
    write(instance, RESULT)
    text = (instance / "docs" / "RESEARCH.md").read_text()
    assert "Perishability: semi-durable · Refresh-by: 20" in text  # an ISO date follows

def test_degraded_synthesis_falls_back_to_confirmed_layer(instance):
    degraded = {"question": "Q", "synthesisDegraded": True, "findings": [],
                "confirmed": [{"claim": "raw claim", "confidence": "high",
                               "vote": "3-0", "source": "https://a.example"}],
                "refuted": []}
    r = write(instance, degraded)
    assert r.returncode == 0, r.stderr
    text = (instance / "docs" / "RESEARCH.md").read_text()
    assert "Synthesis degraded" in text and "raw claim" in text

def test_appends_do_not_clobber(instance):
    write(instance, RESULT)
    second = dict(RESULT, findings=[{"claim": "Second domain claim", "confidence": "high",
                                     "sources": ["https://e.example"], "vote": "3-0"}])
    rj = instance / "r2.json"
    rj.write_text(json.dumps(second))
    r = run_script("doctrine_write.py", argv=[str(rj), str(instance), "--domain", "other topic"])
    assert r.returncode == 0, r.stderr
    text = (instance / "docs" / "RESEARCH.md").read_text()
    assert "study cadence" in text and "other topic" in text

def test_bad_perishability_hard_fails(instance):
    r = write(instance, RESULT, ("--perishability", "eternal"))
    assert r.returncode != 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_doctrine_write.py -v`
Expected: FAIL (doctrine_write.py not found)

- [ ] **Step 3: Write the implementation**

Create `templates/hooks/doctrine_write.py`:

```python
#!/usr/bin/env python3
"""Persist a deep-research result JSON as graded findings in docs/RESEARCH.md.
Engine contract (umbrella spec §4): graded findings + refuted list + caveats,
dated, with a perishability class driving the refresh-by date.
Kernel utility, not an event hook (like validate.py): invoked explicitly, so
hard failures are correct here — no exit-0 swallowing.

Grades use the instance vocabulary (build Stage 2.5): VERIFIED / THIN.
Engine confidence high -> VERIFIED; medium/low -> THIN; refuted -> negatives section.

Usage: doctrine_write.py <result.json> <instance-root> --domain <name>
                         [--perishability durable|semi-durable|perishable]
"""
import json, sys, datetime
from pathlib import Path

GRADE = {"high": "VERIFIED", "medium": "THIN", "low": "THIN"}
REFRESH_DAYS = {"durable": None, "semi-durable": 180, "perishable": 60}

def main():
    args = sys.argv[1:]
    perish = "semi-durable"
    if "--perishability" in args:
        i = args.index("--perishability"); perish = args[i + 1]; del args[i:i + 2]
    if "--domain" not in args or len(args) < 4:
        sys.exit("usage: doctrine_write.py <result.json> <instance-root> --domain <name>"
                 " [--perishability durable|semi-durable|perishable]")
    i = args.index("--domain"); domain = args[i + 1]; del args[i:i + 2]
    if perish not in REFRESH_DAYS:
        sys.exit(f"unknown perishability class: {perish} (want durable|semi-durable|perishable)")
    result = json.loads(Path(args[0]).read_text())
    root = Path(args[1])
    today = datetime.date.today()
    days = REFRESH_DAYS[perish]
    refresh = (today + datetime.timedelta(days=days)).isoformat() if days else "on contradiction"

    lines = [f"## {domain} — researched {today.isoformat()}",
             f"Perishability: {perish} · Refresh-by: {refresh} · Engine: deep-research (3-vote adversarial)",
             ""]
    findings = result.get("findings") or []
    if result.get("synthesisDegraded") or not findings:
        # never lose the verified layer: fall back to raw confirmed claims
        lines.append("_Synthesis degraded — raw verified claims below._")
        for c in result.get("confirmed") or []:
            g = GRADE.get(c.get("confidence") or "low", "THIN")
            lines.append(f"- **{g}** {c['claim']} (vote {c.get('vote', '?')}) — {c.get('source', '')}")
    else:
        for f in findings:
            g = GRADE.get(f.get("confidence") or "low", "THIN")
            lines.append(f"- **{g}** {f['claim']}")
            if f.get("evidence"):
                lines.append(f"  - evidence: {f['evidence']} (vote {f.get('vote', '?')})")
            lines.append(f"  - sources: {', '.join(f.get('sources') or [])}")
    refuted = result.get("refuted") or []
    if refuted:
        lines += ["", "### Refuted — do not build on"]
        for r in refuted:
            lines.append(f"- {r['claim']} (vote {r.get('vote', '?')}, {r.get('source', '')})")
    if result.get("caveats"):
        lines += ["", "### Caveats", str(result["caveats"])]
    lines.append("")

    out = root / "docs" / "RESEARCH.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    prev = out.read_text() if out.exists() else "# Research findings (instance doctrine)\n\n"
    out.write_text(prev + "\n".join(lines) + "\n")
    print(f"wrote {domain}: {len(findings)} findings, {len(refuted)} refuted -> {out}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_doctrine_write.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add templates/hooks/doctrine_write.py tests/test_doctrine_write.py
git commit -m "feat(sp1): doctrine_write.py — deterministic engine-result -> RESEARCH.md persister"
```

---

### Task 3: Scaffolder copies the engine into instances

**Files:**
- Modify: `skills/build/scaffold.py` (after the hooks copy loop, ~line 78)
- Test: `tests/test_scaffold.py` (extend `test_scaffold_layout`)

- [ ] **Step 1: Extend the failing test**

In `tests/test_scaffold.py::test_scaffold_layout`, add two paths to the existing `for rel in [...]` list:

```python
                ".claude/hooks/doctrine_write.py",
                ".claude/workflows/deep-research.js",
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_scaffold.py::test_scaffold_layout -v`
Expected: FAIL on `.claude/workflows/deep-research.js` (doctrine_write.py already rides the existing `templates/hooks` glob loop and passes)

- [ ] **Step 3: Add the copy to scaffold.py**

In `skills/build/scaffold.py`, directly after the hooks copy loop:

```python
    for hook in (T / "hooks").glob("*.py"):
        shutil.copy(hook, target / ".claude" / "hooks" / hook.name)
```

add:

```python
    # research engine: instances get /deep-research natively (plugins can't ship
    # saved workflows, so the scaffolder installs the vendored script per-instance)
    (target / ".claude" / "workflows").mkdir(parents=True)
    shutil.copy(REPO / "skills" / "research" / "deep-research.js",
                target / ".claude" / "workflows" / "deep-research.js")
```

- [ ] **Step 4: Run the full scaffold test file**

Run: `python3 -m pytest tests/test_scaffold.py -v`
Expected: all PASS (including `test_scaffolded_instance_boots_clean` — the new files must not trip the validator; if `validate.py` complains about unknown files, that is a real finding to fix in `validate.py`'s allowlist, not to suppress)

- [ ] **Step 5: Commit**

```bash
git add skills/build/scaffold.py tests/test_scaffold.py
git commit -m "feat(sp1): scaffolder installs vendored deep-research.js into instance workflows"
```

---

### Task 4: `/cairn:research` skill — the engine front door

**Files:**
- Create: `skills/research/SKILL.md`
- Modify: `tests/test_skills_exist.py` (add `research` entry)

- [ ] **Step 1: Extend the failing test**

In `tests/test_skills_exist.py`, add to the dict:

```python
        "research": ["GROUNDING", "scriptPath", "deep-research.js", "doctrine_write.py",
                     "degraded", "Refuted", "decision", "perishability"],
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_skills_exist.py -v`
Expected: FAIL (`skills/research/SKILL.md` missing)

- [ ] **Step 3: Write the skill**

Create `skills/research/SKILL.md` with exactly this content:

````markdown
---
name: research
description: Frame a decision, run the vendored deep-research engine (claim-scaled, 3-vote adversarial), and persist graded findings into the instance's docs/RESEARCH.md
---

# /cairn:research — the research engine

Research serves a **decision, not a topic**. This skill is the mandatory front door to the
engine: the builder (Stage 2.5) and the governor (research proposals) route through this
procedure — never launch the workflow raw.

## Step 1 — Frame (never skip)

Before searching anything, write down:
- **The decision this informs.** Which parameter, design choice, or proposal will change
  based on the answer? If you can't name it, stop — it doesn't clear the research bar.
- **The real question**, restated in your own words, scoped to the decision (widen if the
  decision hinges on an adjacent question; narrow if the topic is broader than the need).
- **What's already settled** — check docs/RESEARCH.md and the manifest first; never
  re-research a finding that is current and VERIFIED.
- If the domain is unfamiliar or fast-moving, run 1-3 orientation searches to map terms —
  reconnaissance only, never findings. 4+ searches means you've started researching
  unverified; stop and launch the engine instead.

## Step 2 — Write the GROUNDING block

```
<framed question — the decision it serves, in one or two sentences>

GROUNDING:
- Breadth: narrow | standard | broad   (be honest — padding narrow questions wastes verification budget)
- Sub-areas needing verified coverage: <each distinct area; each gets its own angle and a verification floor>
- Key terms/entities: <names, jargon, synonyms that make queries land>
- Known primary sources worth fetching: <papers, specs, official docs>
- Already known / do not research: <settled knowledge the engine should skip>
```

The engine sizes the whole run from this (2-8 angles, fetch budget, per-angle verification
floors). A missing GROUNDING block makes it guess from the question text alone.

## Step 3 — Launch

Inside a cairn instance (the normal case — governor re-research, post-scaffold builder runs):

```
Workflow({ scriptPath: ".claude/workflows/deep-research.js", args: "<framed question + GROUNDING>" })
```

From the plugin before an instance exists (builder Stage 2.5, pre-scaffold):

```
Workflow({ scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/research/deep-research.js", args: "<framed question + GROUNDING>" })
```

The run is backgrounded; continue interview work and return when the result notification
arrives. Save the result JSON to a temp file when it completes.

## Step 4 — Persist (the engine contract)

Every run's output is persisted through the deterministic writer — findings never live only
in conversation:

```
python3 .claude/hooks/doctrine_write.py <result.json> <instance-root> \
  --domain "<short domain name>" --perishability <class>
```

(Pre-scaffold, use `${CLAUDE_PLUGIN_ROOT}/templates/hooks/doctrine_write.py` and persist into
the instance directory as soon as it is scaffolded.)

Choose the perishability class honestly — it sets the Refresh-by date the governor sweeps:
- **durable** — mechanisms, human-factors results, math ("on contradiction")
- **semi-durable** — taxonomies' magnitudes, tooling economics (~180 days)
- **perishable** — model capabilities, platform surface, prices (~60 days)

Grades are the instance vocabulary: engine confidence high → **VERIFIED**, medium/low →
**THIN**. Refuted claims land in a "Refuted — do not build on" section — cite them to kill
zombie parameters, never to justify one. Every research-backed parameter cites its finding
from the manifest decisions[] entry (build Stage 2.5 rule, unchanged).

## Degraded mode (no Workflow tool)

Workflows need Pro+/API and can be disabled. If the Workflow tool is unavailable or the
launch is denied:
1. Spawn one general-purpose subagent per GROUNDING sub-area (2-5 total): WebSearch that
   angle, fetch the 2-3 strongest sources, extract falsifiable claims with quotes.
2. For each load-bearing claim, spawn 3 adversarial verifier subagents prompted to REFUTE
   it against sources; ≥2 refutations kill the claim. Default-refute when uncertain.
3. Persist survivors through doctrine_write.py exactly as above, but cap every grade at
   **THIN** — the degraded pass verifies at reduced scale and must not masquerade as the
   full engine. Say so in the section's caveats.

## Contract summary

**In:** a framed decision + GROUNDING block. **Out:** graded findings + refuted list +
caveats appended to `docs/RESEARCH.md`, date-stamped, with a perishability class and
Refresh-by date the governor can sweep. No exceptions: unpersisted research didn't happen.
````

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_skills_exist.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add skills/research/SKILL.md tests/test_skills_exist.py
git commit -m "feat(sp1): /cairn:research skill — framing front door, launch, persist, degraded mode"
```

---

### Task 5: Wire builder, governor, and upgrade to the vendored engine

**Files:**
- Modify: `skills/build/SKILL.md` (Stage 2.5 step 4, lines ~52-57)
- Modify: `skills/review/SKILL.md` (research-proposal bullet, lines ~73-76)
- Modify: `skills/upgrade/SKILL.md` (step 3, hooks-copy paragraph)

- [ ] **Step 1: Rewrite build Stage 2.5 step 4**

In `skills/build/SKILL.md`, replace:

```
4. **Execute — prefer the strongest available engine.** If a deep-research skill or workflow
   exists in this environment (check the available-skills list for e.g. `deep-research`),
   invoke it with the framed questions. Otherwise run the built-in fallback: for each
   question, spawn 2-3 search subagents on DIFFERENT angles (academic, practitioner,
   contrarian); fetch primary sources over listicles; then for each load-bearing claim spawn
   one adversarial verifier prompted to REFUTE it against the source. Keep only survivors.
```

with:

```
4. **Execute — via the vendored engine.** Follow the /cairn:research skill
   (${CLAUDE_PLUGIN_ROOT}/skills/research/SKILL.md): frame each question as the decision it
   serves, write a GROUNDING block, and launch the plugin's own deep-research workflow
   (Workflow({scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/research/deep-research.js", ...}) —
   pre-scaffold there is no instance copy yet). If the Workflow tool is unavailable, use
   that skill's degraded mode: 2-5 angle subagents, then per-claim adversarial verifiers
   prompted to REFUTE (≥2/3 refutations kill); degraded-mode grades cap at THIN.
```

- [ ] **Step 2: Point the governor's research proposals at the engine**

In `skills/review/SKILL.md`, replace:

```
- **Research is a valid proposal.** If a friction cluster traces to a design decision the
  manifest grades BET or THIN, propose a research run (the build skill's Stage 2.5 protocol:
  frame the decision, search primary sources, adversarially verify, update docs/RESEARCH.md
  and re-parametrize) instead of guessing a new value. Also flag docs/RESEARCH.md if its
```

with:

```
- **Research is a valid proposal.** If a friction cluster traces to a design decision the
  manifest grades BET or THIN, propose a research run via the /cairn:research skill (frame
  the decision, GROUNDING block, launch the instance's own .claude/workflows/deep-research.js,
  persist through doctrine_write.py) instead of guessing a new value. Also flag docs/RESEARCH.md if its
```

- [ ] **Step 3: Teach upgrade about the instance workflow copy**

In `skills/upgrade/SKILL.md` step 3, after the sentence ending `(report each file replaced).`, insert:

```
   The research workflow is plugin-owned too: copy
   ${CLAUDE_PLUGIN_ROOT}/skills/research/deep-research.js over the instance's
   .claude/workflows/deep-research.js (create the directory if a pre-0.3.0 instance
   lacks it).
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m pytest tests/ -v`
Expected: all PASS — `test_skills_exist.py` build tokens ("deep-research", "REFUTE", "RESEARCH.md") all still present in the new text; review tokens unchanged.

- [ ] **Step 5: Commit**

```bash
git add skills/build/SKILL.md skills/review/SKILL.md skills/upgrade/SKILL.md
git commit -m "feat(sp1): route builder/governor research through the vendored engine; upgrade manages instance workflow copy"
```

---

### Task 6: Version bump, changelog, README

**Files:**
- Modify: `.claude-plugin/plugin.json` (version 0.2.0 → 0.3.0)
- Modify: `CHANGELOG.md` (new 0.3.0 section at top, after `# Changelog`)
- Modify: `README.md` (command table row)

- [ ] **Step 1: Bump version**

In `.claude-plugin/plugin.json`: `"version": "0.2.0"` → `"version": "0.3.0"`.

- [ ] **Step 2: Changelog entry**

Insert after the `# Changelog` line in `CHANGELOG.md`:

```markdown
## 0.3.0 — vendored research engine (SP1 of the level-zero umbrella)

- **`/cairn:research`** — the engine front door: frame the decision, write a GROUNDING block, launch, persist. Builder Stage 2.5 and governor research proposals now route through it; no dependency on any globally-installed research skill.
- **Vendored deep-research workflow** — ships as a skill supporting file (plugins can't ship saved workflows) launched via `scriptPath`; the scaffolder installs a copy into each instance's `.claude/workflows/` so instances get `/deep-research` natively; `/cairn:upgrade` keeps it current.
- **`doctrine_write.py`** — deterministic engine-result → `docs/RESEARCH.md` persister: instance grades (VERIFIED/THIN), refuted negatives, caveats, date stamp, and a perishability class (durable / semi-durable / perishable) that sets a Refresh-by date for future governor sweeps.
- **Degraded mode** — no Workflow tool (non-Pro plan, disabled, denied) → subagent fallback at reduced scale with grades capped at THIN.

Umbrella spec: docs/superpowers/specs/2026-07-23-level-zero-umbrella-design.md (SP2-SP4 follow).
```

- [ ] **Step 3: README command table**

In `README.md`, add a row to the command table after the `/cairn:build` row:

```markdown
| `/cairn:research` | The research engine: frames a decision, runs a claim-scaled 3-vote adversarial deep-research workflow, persists graded findings (with refresh-by dates) into the instance's `docs/RESEARCH.md`. Used by build and review; callable directly. |
```

- [ ] **Step 4: Run the full suite one last time**

Run: `python3 -m pytest tests/ -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/plugin.json CHANGELOG.md README.md
git commit -m "feat: 0.3.0 — vendored research engine (/cairn:research, doctrine_write, instance workflow install)"
```

---

## Verification (after all tasks)

1. `python3 -m pytest tests/ -v` — full suite green.
2. Smoke: scaffold a throwaway instance into a temp dir (`python3 skills/build/scaffold.py <cfg.json> /tmp/smoke-inst` with the CFG from `tests/test_scaffold.py`), confirm `.claude/workflows/deep-research.js` and `.claude/hooks/doctrine_write.py` exist in it, then run `doctrine_write.py` against a hand-made 2-finding result JSON and read the produced `docs/RESEARCH.md`.
3. Confirm no test references the user's global `~/.claude/workflows/deep-research.js` — the plugin must be self-contained.
