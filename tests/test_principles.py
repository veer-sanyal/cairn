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
