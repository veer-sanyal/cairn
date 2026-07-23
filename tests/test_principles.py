import re
from conftest import REPO

TEXT = (REPO / "docs" / "PRINCIPLES.md").read_text()

def blocks():
    """Split file into {principle number: block text}."""
    parts = re.split(r"\n## (\d+)\. ", TEXT)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}

def test_headers_present_and_unique():
    b = blocks()
    for n in range(1, 21):          # extended to 25 by later tasks
        assert n in b, f"P{n} missing"
    nums = re.findall(r"\n## (\d+)\. ", TEXT)
    assert len(nums) == len(set(nums)), "duplicate principle number"

def test_every_principle_annotated():
    for n, block in blocks().items():
        first_line = block.split("\n", 1)[1].split("\n", 1)[0]
        assert re.search(r"Perishability: (durable|semi-durable|perishable)", first_line), \
            f"P{n} missing/misplaced annotation line"
        assert re.search(r"Verified: 20\d\d-\d\d", first_line), f"P{n} missing Verified date"

def test_p16_p17_tokens():
    b = blocks()
    for tok in ["MAST", "self-correct", "design", "compound"]:
        assert tok in b[16], f"P16 missing '{tok}'"
    for tok in ["pass^k", "coin-flip", "pilot", "probe"]:
        assert tok in b[17], f"P17 missing '{tok}'"

def test_p18_tokens():
    b = blocks()
    for tok in ["Goodhart", "optimization power", "regressional", "causal", "revalidat"]:
        assert tok in b[18], f"P18 missing '{tok}'"

def test_p19_tokens():
    b = blocks()
    for tok in ["rubber-stamp", "ask-budget", "act/ask", "blast", "override", "inhibitive"]:
        assert tok in b[19], f"P19 missing '{tok}'"

def test_p20_tokens():
    b = blocks()
    for tok in ["single-writer", "cascade", "15x", "escalate", "best-of-n"]:
        assert tok in b[20], f"P20 missing '{tok}'"

def test_grade_vocabulary_defined():
    head = TEXT.split("## 1. ", 1)[0]
    for g in ["[VERIFIED]", "[PREPRINT]", "[BET]", "[REFUTED]"]:
        assert g in head, f"grade {g} not defined in header"
