import datetime
import re
from conftest import REPO

TEXT = (REPO / "docs" / "PRINCIPLES.md").read_text()

def blocks(text=TEXT):
    """Split file into {principle number: block text}."""
    parts = re.split(r"\n## (\d+)\. ", text)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}

def months_old(ym, today):
    y, m = map(int, ym.split("-"))
    return (today.year - y) * 12 + (today.month - m)

def expired_principles(text, today):
    """Doctrine expiry sweep for THIS repo (P22 annual ceiling; locked decision 6).
    Returns [(principle number, reason)]. 'Verified: n/a' is exempt — reserved for
    P24, the one [BET]-through-and-through principle with no research round."""
    out = []
    for n, block in blocks(text).items():
        line = block.split("\n", 1)[1].split("\n", 1)[0]
        m = re.search(r"Verified: (20\d\d-\d\d|n/a)", line)
        if not m:
            continue  # format is test_every_principle_annotated's job
        if m.group(1) == "n/a":
            continue
        age = months_old(m.group(1), today)
        if age > 12:
            out.append((n, f"verified {m.group(1)} is {age} months old (>12 ceiling)"))
        elif age > 6 and "Perishability: perishable" in line:
            out.append((n, f"perishable, verified {m.group(1)} is {age} months old (>6)"))
    return out

def test_headers_present_and_unique():
    b = blocks()
    for n in range(1, 25):
        assert n in b, f"P{n} missing"
    nums = re.findall(r"\n## (\d+)\. ", TEXT)
    assert len(nums) == len(set(nums)), "duplicate principle number"

def test_every_principle_annotated():
    for n, block in blocks().items():
        first_line = block.split("\n", 1)[1].split("\n", 1)[0]
        assert re.search(r"Perishability: (durable|semi-durable|perishable)", first_line), \
            f"P{n} missing/misplaced annotation line"
        assert re.search(r"Verified: (20\d\d-\d\d|n/a)", first_line), f"P{n} missing Verified date"

def test_p16_p17_tokens():
    b = blocks()
    for tok in ["MAST", "self-correct", "design", "compound", "HORIZON"]:
        assert tok in b[16], f"P16 missing '{tok}'"
    for tok in ["pass^k", "coin-flip", "pilot", "probe"]:
        assert tok in b[17], f"P17 missing '{tok}'"

def test_p18_tokens():
    b = blocks()
    for tok in ["Goodhart", "optimization power", "regressional", "causal", "revalidat"]:
        assert tok in b[18], f"P18 missing '{tok}'"

def test_p19_tokens():
    b = blocks()
    for tok in ["rubber-stamp", "ask-budget", "act/ask", "blast", "override", "inhibitive", "over-constrain"]:
        assert tok in b[19], f"P19 missing '{tok}'"

def test_p20_tokens():
    b = blocks()
    for tok in ["single-writer", "cascade", "15x", "escalate", "best-of-n"]:
        assert tok in b[20], f"P20 missing '{tok}'"

def test_p21_p22_tokens():
    b = blocks()
    for tok in ["rubric", "kappa", "calibrat", "trajectory", "mean"]:
        assert tok in b[21], f"P21 missing '{tok}'"
    for tok in ["living", "event-triggered", "self-detect", "surveillance", "ceiling"]:
        assert tok in b[22], f"P22 missing '{tok}'"

def test_p23_p24_tokens():
    b = blocks()
    for tok in ["hook", "census", "skill", "workflow", "mechanisms-claude-code"]:
        assert tok in b[23], f"P23 missing '{tok}'"
    # P24 flipped BET → VERIFIED mechanism in R10: continuous shrinkage handover,
    # the old "first governor review" checkpoint refuted. Tokens track the new doctrine.
    for tok in ["Cold start", "handover", "shrinkage", "James-Stein", "REFUTED"]:
        assert tok in b[24], f"P24 missing '{tok}'"

def _synth(*annots):
    """Build a minimal PRINCIPLES-shaped text from annotation lines."""
    return "head\n" + "".join(
        f"\n## {i}. Title {i}\n{a}\n\nbody\n" for i, a in enumerate(annots, 1))

def test_expiry_checker_flags_synthetic_old_dates():
    today = datetime.date(2026, 7, 24)
    text = _synth(
        "Perishability: durable · Verified: 2025-06 · Round: R1",       # 13 mo — expired
        "Perishability: perishable · Verified: 2025-12 · Round: R2",    # 7 mo perishable — expired
        "Perishability: perishable · Verified: 2026-02 · Round: R3",    # 5 mo perishable — fine
        "Perishability: durable · Verified: 2025-08 · Round: R4",       # 11 mo durable — fine
        "Perishability: durable · Verified: n/a · Round: none",         # n/a — exempt
    )
    assert [n for n, _ in expired_principles(text, today)] == [1, 2]

def test_expiry_boundary_exact_ceilings_pass():
    today = datetime.date(2026, 7, 24)
    text = _synth(
        "Perishability: durable · Verified: 2025-07 · Round: R1",       # exactly 12 mo
        "Perishability: perishable · Verified: 2026-01 · Round: R2",    # exactly 6 mo
    )
    assert expired_principles(text, today) == []

def test_no_principle_expired_in_real_file():
    stale = expired_principles(TEXT, datetime.date.today())
    assert not stale, f"doctrine expired: {stale}"

def test_no_principle_uses_verified_na():
    # Pre-R10, P24 was the one un-researched "Verified: n/a" explicit BET. R10 settled it
    # (Round: R10, dated), so every shipped principle is now dated/researched — no principle
    # may carry the n/a marker. The expiry checker still *exempts* n/a as a capability
    # (see test_expiry_checker_flags_synthetic_old_dates), but no real doctrine uses it.
    na = [n for n, block in blocks().items()
          if "Verified: n/a" in block.split("\n", 1)[1].split("\n", 1)[0]]
    assert na == [], f"post-R10 every principle is dated; 'Verified: n/a' no longer used, got {na}"

def test_grade_vocabulary_defined():
    head = TEXT.split("## 1. ", 1)[0]
    for g in ["[VERIFIED]", "[PREPRINT]", "[BET]", "[REFUTED]"]:
        assert g in head, f"grade {g} not defined in header"
