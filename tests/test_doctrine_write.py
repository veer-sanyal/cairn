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
