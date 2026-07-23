# SP2: Level-Zero Doctrine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PRINCIPLES.md v2 — synthesize R5–R9 + the mechanisms reference into P16–P24, retrofit P1–P15 with perishability/verified annotations, guarded by a new structural test.

**Architecture:** Content-synthesis tasks, one research round per task so no task needs more than one ~100KB JSON in context. Each task appends its principles in numbered position, extends `tests/test_principles.py` with its tokens (test-first), and commits. P-numbering P1–P15 is frozen; content edits to existing principles are forbidden (annotation line insertion only). Spec: `docs/superpowers/specs/2026-07-23-sp2-level-zero-doctrine-design.md` — its §"Structure decisions" (format, annotation schema, curation rule for refuted entries) binds every task. The umbrella spec §3 (`2026-07-23-level-zero-umbrella-design.md`) lists the headline findings each principle MUST encode; each task below names them.

**Tech Stack:** markdown + pytest. Source JSONs have fields: `findings[{claim, confidence, sources, evidence, vote}]`, `refuted[...]`, `caveats`, `openQuestions`, `summary`.

**Content tasks are judgment-heavy:** implementers must read the actual round JSON (not just this plan), select and compress accurately, and preserve vote counts/sources. Confidence→grade mapping for doctrine: finding confidence `high` → [VERIFIED]; `medium` → [VERIFIED — medium] or [PREPRINT] per the finding's source quality (preprint-only evidence → [PREPRINT]); `low` → [PREPRINT]. Never upgrade; when unsure, grade down.

---

### Task 1: Structural test + retrofit P1–P15 annotations + annotation schema doc

**Files:**
- Create: `tests/test_principles.py`
- Modify: `docs/PRINCIPLES.md` (header block + one annotation line under each of P1–P15)

- [ ] **Step 1: Write the failing test**

Create `tests/test_principles.py`:

```python
import re
from conftest import REPO

TEXT = (REPO / "docs" / "PRINCIPLES.md").read_text()

def blocks():
    """Split file into {principle number: block text}."""
    parts = re.split(r"\n## (\d+)\. ", TEXT)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}

def test_headers_present_and_unique():
    b = blocks()
    for n in range(1, 16):          # extended to 25 by later tasks
        assert n in b, f"P{n} missing"
    nums = re.findall(r"\n## (\d+)\. ", TEXT)
    assert len(nums) == len(set(nums)), "duplicate principle number"

def test_every_principle_annotated():
    for n, block in blocks().items():
        first_line = block.split("\n", 1)[1].split("\n", 1)[0]
        assert re.search(r"Perishability: (durable|semi-durable|perishable)", first_line), \
            f"P{n} missing/misplaced annotation line"
        assert re.search(r"Verified: 20\d\d-\d\d", first_line), f"P{n} missing Verified date"

def test_grade_vocabulary_defined():
    head = TEXT.split("## 1. ", 1)[0]
    for g in ["[VERIFIED]", "[PREPRINT]", "[BET]", "[REFUTED]"]:
        assert g in head, f"grade {g} not defined in header"
```

- [ ] **Step 2: Run it, verify the annotation test FAILS**

Run: `python3 -m pytest tests/test_principles.py -v`
Expected: `test_headers_present_and_unique` PASS, `test_every_principle_annotated` FAIL (no annotation lines yet), `test_grade_vocabulary_defined` PASS.

- [ ] **Step 3: Retrofit annotation lines**

In `docs/PRINCIPLES.md`, insert directly under each `## N. title` header (as the immediately following line) an annotation line. Do NOT change any other text of P1–P15. Assignments (classes follow umbrella §3.10: durable = human-factors/math/mechanisms, semi-durable = magnitudes/tooling economics, perishable = model-capability/platform facts):

```
P1  (context rot):            Perishability: semi-durable · Verified: 2026-07 · Round: R1
P2  (facts in files):         Perishability: semi-durable · Verified: 2026-07 · Round: R1
P3  (sub-agent fan-out):      Perishability: semi-durable · Verified: 2026-07 · Round: R1
P4  (index-first):            Perishability: semi-durable · Verified: 2026-07 · Round: R1
P5  (tiered memory):          Perishability: durable · Verified: 2026-07 · Round: R1
P6  (consolidation):          Perishability: durable · Verified: 2026-07 · Round: R2
P7  (externalization):        Perishability: durable · Verified: 2026-07 · Round: R1
P8  (instruction drift):      Perishability: perishable · Verified: 2026-07 · Round: R2
P9  (deterministic gates):    Perishability: perishable · Verified: 2026-07 · Round: R2
P10 (bounded self-improve):   Perishability: durable · Verified: 2026-07 · Round: R2
P11 (telemetry schema):       Perishability: semi-durable · Verified: 2026-07 · Round: R3
P12 (metric contract):        Perishability: durable · Verified: 2026-07 · Round: R3
P13 (abandonment typed):      Perishability: durable · Verified: 2026-07 · Round: R3
P14 (elicitation):            Perishability: durable · Verified: 2026-07 · Round: R4
P15 (prior art):              Perishability: perishable · Verified: 2026-07 · Round: R4
```

Also update the header block's grade-definition paragraph: after the existing grade definitions, append one sentence:

```
Every principle carries an annotation line: `Perishability: durable|semi-durable|perishable · Verified: YYYY-MM · Round: R<n>` — durable refreshes on contradiction only, semi-durable within ~2 releases, perishable is probe-not-recall (short windows). The governor's expiry sweep (SP3) reads these fields.
```

And update the "Rounds:" sentence in the header to note R5–R9 exist (full provenance lands in Task 7).

- [ ] **Step 4: Run tests, verify PASS**

Run: `python3 -m pytest tests/test_principles.py -v` → 3 PASS. Full suite: `python3 -m pytest tests/ -q` → all pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_principles.py docs/PRINCIPLES.md
git commit -m "feat(sp2): principle annotation schema + P1-P15 perishability retrofit + structural test"
```

---

### Task 2: P16 failure taxonomy + P17 capability frontier (from R5)

**Files:**
- Modify: `docs/PRINCIPLES.md` (append P16, P17 after P15, before "## Research provenance")
- Modify: `tests/test_principles.py`

- [ ] **Step 1: Extend the failing test**

In `tests/test_principles.py`, change the header range to `range(1, 18)` and add:

```python
def test_p16_p17_tokens():
    b = blocks()
    for tok in ["MAST", "self-correct", "design", "compound"]:
        assert tok in b[16], f"P16 missing '{tok}'"
    for tok in ["pass^k", "coin-flip", "pilot", "probe"]:
        assert tok in b[17], f"P17 missing '{tok}'"
```

Run: `python3 -m pytest tests/test_principles.py -v` → FAIL (P16/P17 missing).

- [ ] **Step 2: Read the source round**

Read `docs/research/research-round5-failure-capability.json` in full — findings, refuted, caveats. This is the authority; the umbrella's headline list (below) is the minimum, not the ceiling.

- [ ] **Step 3: Write P16 and P17**

Append after P15, following the spec's format (header · annotation line · graded findings with sources and votes · curated refuted · design implications). Annotation lines:
- P16: `Perishability: durable (taxonomy) — magnitudes semi-durable · Verified: 2026-07 · Round: R5`
- P17: `Perishability: perishable · Verified: 2026-07 · Round: R5`

P16 (suggested title: "Agentic failure is taxonomizable — and predominantly a design problem") MUST encode: MAST 14-mode/3-category canonical taxonomy (NeurIPS 2025, kappa 0.88); 41–86.7% failure rates across 7 SOTA frameworks; failures predominantly design flaws with +9.4/+15.6pp single-fix gains [VERIFIED — medium, 2-1 vote — grade honestly]; agents rarely self-correct (91.49% needed explicit user correction, 20,574 sessions); verifier-ran is a weak signal (superficial verification passes broken output, FM-3.2/3.3 percentages OK to cite, other sub-mode percentages REFUTED — carry that refuted entry); errors compound and self-condition over horizon length. Design implications: telemetry failure_mode tags (SP3), external correction loops, checked verifiers.

P17 (suggested title: "The capability frontier is probed, never recalled") MUST encode: pass^k not pass@k (pass^8 <25% where single-trial looked fine); METR horizons are 50% coin-flip thresholds not guarantees; long-horizon difficulty is domain-structural, not human-duration-estimated; cheap pilots work ($4.26/1,368-episode pilot preceding a 23K-episode study); frontier claims carry short refresh windows. Design implications: builder runs small pass^k probes before committing designs to "the model can do X"; probe results land in manifest as dated claims.

- [ ] **Step 4: Run tests** → `python3 -m pytest tests/test_principles.py -v` all PASS; full suite green.

- [ ] **Step 5: Commit** — `git add docs/PRINCIPLES.md tests/test_principles.py && git commit -m "feat(sp2): P16 failure taxonomy + P17 capability frontier (R5)"`

---

### Task 3: P18 objective design & Goodhart (from R7)

Same 5-step shape as Task 2. Test range → `range(1, 19)`; tokens:

```python
def test_p18_tokens():
    b = blocks()
    for tok in ["Goodhart", "optimization power", "regressional", "causal", "revalidat"]:
        assert tok in b[18], f"P18 missing '{tok}'"
```

Read `docs/research/research-round7-objective-design-goodhart.json` in full.

P18 (suggested title: "Objectives corrupt under optimization — design for it") annotation: `Perishability: durable · Verified: 2026-07 · Round: R7`. MUST encode: four Goodhart mechanisms (regressional/extremal/causal/adversarial) each needing a different mitigation; input levers must be causally validated and extreme-range behavior can't be assumed; severity scales with optimization power (agentic systems worst case, verified verbatim); LM agents specification-game zero-shot; Skalse NeurIPS 2022 — proxy rewards theoretically hackable except degenerate cases → no metric contract is permanently safe, scheduled proxy revalidation is a lifecycle event; north-star non-actionability now mechanism-backed (cross-reference P12). Carry the honest caveat: leading/lagging-indicator sub-area weak — grade those [BET] (two canonical claims refuted 0-3; name them in the refuted entries). Design implications: governor proxy-revalidation sweep (SP3); metric-contract interview cites mechanisms not folklore.

Commit: `feat(sp2): P18 objective design and Goodhart resistance (R7)`

---

### Task 4: P19 human-agent boundary (from R8)

Same shape. Test range → `range(1, 20)`; tokens:

```python
def test_p19_tokens():
    b = blocks()
    for tok in ["rubber-stamp", "ask-budget", "act/ask", "blast", "override", "inhibitive"]:
        assert tok in b[19], f"P19 missing '{tok}'"
```

Read `docs/research/research-round8-human-agent-boundary.json` in full.

P19 (suggested title: "Autonomy is graded by blast radius; asks are a budget") annotation: `Perishability: durable · Verified: 2026-07 · Round: R8`. MUST encode: humans structurally bad at sustained oversight of reliable automation (33% vs 82% detection, expertise doesn't fix it); uniform per-action gating rubber-stamps (93% approval, Anthropic first-party — note the companion 84%-mechanism claim was REFUTED, carry it); Horvitz act/ask/do-nothing with expected utility × blast radius (cite Anthropic likelihood×damage); ask FREQUENCY drives abandonment (HR 0.78), so asks are a rationed budget spent where load-bearing; inhibitive friction (forced interaction) up to −50% unsafe choices and survives habituation, passive warnings don't; token override channel doubles adoption of imperfect-but-superior automation; oversight-theater result (Green: mandates that can't be performed legitimize flawed systems). Cross-reference P13 (trust & adoption fold-in, umbrella §3.11). Design implications: every instance carries an ask-budget + blast-radius table (SP3); irreversible+external actions never autonomous; keep a user-editable knob even when data says the default is right.

Commit: `feat(sp2): P19 human-agent boundary — delegation, trust, friction, blast radius (R8)`

---

### Task 5: P20 orchestration & model tiering (from R9)

Same shape. Test range → `range(1, 21)`; tokens:

```python
def test_p20_tokens():
    b = blocks()
    for tok in ["single-writer", "cascade", "15x", "escalate", "best-of-n"]:
        assert tok in b[20], f"P20 missing '{tok}'"
```

Read `docs/research/research-round9-orchestration-tiering.json` in full.

P20 (suggested title: "Default single-threaded; fan-out is bought with tokens") annotation: `Perishability: semi-durable · Verified: 2026-07 · Round: R9`. MUST encode: complexity ladder (direct call → single agent+tools → multi-agent), lowest rung that reliably works, escalate on measurement; multi-agent fits research-shaped breadth (90.2% gain WITH ~15x tokens; token budget explains ~80% of variance — fan-out is parallel token spend, not magic; upgrading the model beat doubling budget); coding/write-heavy is a poor fit; single-writer principle (readers/advisors many, writer one) [VERIFIED — medium, practitioner doctrine — grade honestly]; cascade routing cheap-first with escalation (50–98% cost reduction at ~parity) is the strongest cost lever; quality-over-diversity: Self-MoA/best-of-n from one strong model beats heterogeneous swarms, 2-model consistency-switch ~34% fewer samples [PREPRINT where preprint-only]; subagent delegation criteria (do/don't list from R9). Carry 3–6 of the 15 refuted claims — prioritize the folk beliefs: heterogeneous-swarm superiority, debate-panel superiority on knowledge tasks, any refuted token/cost figures. Cross-reference P3. Design implications: the builder's orchestration selector (SP3) encodes the ladder + cascade, not the folk version.

Commit: `feat(sp2): P20 orchestration and model tiering (R9)`

---

### Task 6: P21 verification & evals + P22 epistemics & decay (from R6)

Same shape. Test range → `range(1, 23)`; tokens:

```python
def test_p21_p22_tokens():
    b = blocks()
    for tok in ["rubric", "kappa", "calibrat", "trajectory", "mean"]:
        assert tok in b[21], f"P21 missing '{tok}'"
    for tok in ["living", "event-triggered", "self-detect", "surveillance", "ceiling"]:
        assert tok in b[22], f"P22 missing '{tok}'"
```

Read `docs/research/research-round6-verification-epistemics.json` in full.

P21 (suggested title: "Judges are instruments — rubric-first, calibrated, probabilistic") annotation: `Perishability: durable (methods) — magnitudes semi-durable · Verified: 2026-07 · Round: R6`. MUST encode: rubric > reference answers (0.666→0.591 vs →0.638 ablation); extremes-only score descriptions suffice; mean-of-samples beats greedy (judge nondeterminism is an asset if sampled+averaged); CoT adds little ONCE the rubric is good (conditionality is load-bearing — the unscoped version was refuted 0-3, carry it); judge biases (position, verbosity, self-preference, sycophancy); even 3-model ensembles only kappa 0.432 vs humans with conservative skew → calibrate against human labels, treat verdicts as P(correct); trajectory/stage-level decomposition (faults propagate ~62% to wrong answers, outcome metrics can't localize); binary verdicts: report kappa + one correlation (all others collapse — mathematical). Design implications: instances that build judges owe a human-labeled calibration set (an ask-budget expense); verifiers must record what they checked (ties to P16).

P22 (suggested title: "Knowledge expires on events, not clocks — and models can't feel it") annotation: `Perishability: durable · Verified: 2026-07 · Round: R6`. MUST encode: living-systematic-review discipline — event-triggered staleness (does new evidence change conclusions?), cheap continuous surveillance decoupled from expensive re-verification, entry/exit criteria (decision priority × low certainty × likely new evidence), ~6-month max incorporation window, hard annual re-review ceiling; models can't self-detect stale knowledge (~55%, near coinflip) and comply with stale premises → expiry triggers must be structural (dated claims, dependency graphs, census diffs), never model self-assessment. Design implications: the perishability annotations in THIS file + doctrine_write's Refresh-by dates are the structural triggers; governor expiry sweep (SP3) reads them.

Commit: `feat(sp2): P21 verification and evals + P22 epistemics and decay (R6)`

---

### Task 7: P23 mechanism selection + P24 cold start + provenance + release

**Files:**
- Modify: `docs/PRINCIPLES.md` (P23, P24, updated "## Research provenance")
- Modify: `tests/test_principles.py` (range → `range(1, 25)`, final tokens)
- Modify: `.claude-plugin/plugin.json` (0.3.0 → 0.4.0), `CHANGELOG.md`

- [ ] **Step 1: Extend the failing test** — range to `range(1, 25)`, add:

```python
def test_p23_p24_tokens():
    b = blocks()
    for tok in ["hook", "census", "skill", "workflow", "mechanisms-claude-code"]:
        assert tok in b[23], f"P23 missing '{tok}'"
    for tok in ["cold start", "BET", "first governor review"]:
        assert tok in b[24], f"P24 missing '{tok}'"
```

- [ ] **Step 2: Write P23** — annotation `Perishability: perishable · Verified: 2026-07 · Round: docs-verified (claude-code-guide)`. ~15 lines: the selection decision tree (fires-automatically→hook; reusable judgment procedure→skill; context-bloating side task→subagent; many-agents/stages→workflow; external source of truth→MCP; every-session facts→CLAUDE.md; distribution→plugin); context-cost logic (resident vs on-demand is the first question); census enumerability consequences (MCP servers enumerable, tool schemas not, no registry-search API → rung-2 of the data-access ladder is manual-assisted); cite `docs/research/research-mechanisms-claude-code-2026-07.md` as the detail file with its refresh-by convention.

- [ ] **Step 3: Write P24** — annotation `Perishability: durable · Verified: n/a · Round: none — explicit BET`. ~10 lines: a fresh instance has zero telemetry; defensible defaults come from level-zero doctrine (ask-budget, blast-radius table, single-writer) plus the build-time research round; control shifts to instance data on a declared schedule — the first governor review is the handover point; graded [BET] end to end (no dedicated round; umbrella gaps ledger names it) — revisit if it earns evidence.

- [ ] **Step 4: Update provenance** — extend the "## Research provenance" section with one row each for R5–R9 (agents, confirmed/refuted counts from each JSON's `stats`, JSON filename) and the mechanisms doc (docs-verified, claude-code-guide agent, 2026-07-23).

- [ ] **Step 5: Release chores** — plugin.json `0.4.0`; CHANGELOG entry after `# Changelog`:

```markdown
## 0.4.0 — level-zero doctrine (SP2 of the level-zero umbrella)

- **PRINCIPLES.md v2** — nine new principles from research rounds R5–R9 (~860 verification agents, 3-vote adversarial): P16 failure taxonomy, P17 capability frontier & probing, P18 Goodhart-resistant objectives, P19 human-agent boundary (ask-budgets, blast radius), P20 orchestration & model tiering, P21 verification & eval design, P22 epistemics & knowledge decay, P23 mechanism selection, P24 cold start [BET].
- **Perishability annotations** — every principle (P1–P24) now carries `Perishability · Verified · Round`; durable refreshes on contradiction, semi-durable within ~2 releases, perishable is probe-not-recall. This is the structural expiry metadata the governor's SP3 sweep will read.
- **Curated [REFUTED] ledger** — folk claims that failed 3-vote verification (fixed sub-mode percentages, heterogeneous-swarm superiority, unscoped CoT-judging gains, ...) are carried as do-not-build-on entries.

Doctrine only — no behavior changes. SP3 (builder/governor wiring) follows.
```

- [ ] **Step 6: Full suite + coherence read** — `python3 -m pytest tests/ -q` all green; read PRINCIPLES.md end-to-end once for numbering, cross-references (P18↔P12, P19↔P13, P20↔P3, P22↔annotation schema), and no unrendered placeholders.

- [ ] **Step 7: Commit** — `git add docs/PRINCIPLES.md tests/test_principles.py .claude-plugin/plugin.json CHANGELOG.md && git commit -m "feat: 0.4.0 — level-zero doctrine complete (P16-P24, perishability annotations, provenance)"`

---

## Verification (after all tasks)

1. `python3 -m pytest tests/ -q` green.
2. Spot-check three principles against their source JSONs (one vote count, one magnitude, one refuted claim each) — synthesis must not have drifted from the verified layer.
3. `grep -c "Perishability:" docs/PRINCIPLES.md` → 24.
4. Confirm P1–P15 body text is untouched: `git diff main -- docs/PRINCIPLES.md` shows only annotation-line insertions and header/provenance edits in the existing sections.
