from pathlib import Path
from conftest import REPO

def test_skills_have_frontmatter_and_load_bearing_content():
    for name, must_contain in {
        "build": ["scaffold.py", "own words", "pairwise", "north star",
                  "RESEARCH.md", "REFUTE", "deep-research",
                  "census", "rung", "pass^k", "boundary", "ask_budget",
                  "single-threaded", "Causal validity", "concealment"],
        "review": ["review-in-progress", "SKIP", "MERGE", "INSERT", "BUILD", "PARK", "REJECT",
                   "RESEARCH.md",
                   "research_expired", "census_stale", "proxy_revalidation", "failure_mode",
                   "de-automat"],
        "upgrade": ["merge.py", "managed-by-cairn", ".cairn-new"],
        "research": ["GROUNDING", "scriptPath", "deep-research.js", "doctrine_write.py",
                     "degraded", "Refuted", "decision", "perishability"],
        "audit": ["manifest.json", "/cairn:review", "north star", "ladder", "file:line",
                  "BUILD", "PARK", "REJECT", "AUDIT.md", "blast", "dirty tree"],
    }.items():
        p = REPO / "skills" / name / "SKILL.md"
        text = p.read_text()
        assert text.startswith("---"), f"{name}: missing frontmatter"
        for token in must_contain:
            assert token in text, f"{name}: missing '{token}'"
