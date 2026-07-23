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
