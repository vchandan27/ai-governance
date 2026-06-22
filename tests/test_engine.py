from app.engine import get_engine
from app.frameworks import load_crosswalk, load_frameworks
from app.schemas import CoverageStatus

GOOD_POLICY = """
Our AI Governance Board owns the AI policy and assigns roles and
responsibilities and accountability across teams.

We maintain a risk management system with an iterative risk assessment and
risk mitigation process across the AI lifecycle.

Training data is reviewed for data quality, representativeness and bias
detection; we document data provenance and data governance.

Customer-facing decisions include human oversight with a human-in-the-loop who
can override or stop the system.

We inform users via AI disclosure when they interact with a chatbot and we
provide instructions for use.

Deployed systems use post-market monitoring and incident reporting for serious
incidents.
"""

EMPTY_POLICY = "This document is about office furniture procurement and catering."


def test_frameworks_load():
    fws = load_frameworks()
    assert {"eu_ai_act", "iso_42001", "nist_ai_rmf"} <= set(fws.keys())
    for fw in fws.values():
        assert fw.controls
        for c in fw.controls:
            assert c.keywords


def test_crosswalk_loads():
    themes = load_crosswalk()
    assert themes
    assert any(t.id == "risk_management" for t in themes)


def test_good_policy_has_coverage():
    engine = get_engine()
    result = engine.analyze(GOOD_POLICY, ["eu_ai_act", "iso_42001", "nist_ai_rmf"])
    assert result.summary.total_controls > 0
    assert result.summary.covered > 0
    assert result.summary.overall_score > 0
    # Risk management should be detected for EU AI Act.
    eu = next(f for f in result.frameworks if f.framework_id == "eu_ai_act")
    rm = next(c for c in eu.controls if c.control_id == "EUAIA-A9")
    assert rm.status in (CoverageStatus.COVERED, CoverageStatus.PARTIAL)
    assert rm.evidence  # should have supporting evidence


def test_empty_policy_has_gaps():
    engine = get_engine()
    result = engine.analyze(EMPTY_POLICY, ["eu_ai_act"])
    assert result.summary.gaps > 0
    # An unrelated document should have a low overall score.
    assert result.summary.overall_score < 40


def test_recommendations_present_for_gaps():
    engine = get_engine()
    result = engine.analyze(EMPTY_POLICY, ["eu_ai_act"])
    gaps = [c for c in result.frameworks[0].controls if c.status == CoverageStatus.GAP]
    assert gaps
    assert all(c.recommendation for c in gaps)


def test_invalid_framework_raises():
    engine = get_engine()
    try:
        engine.analyze(GOOD_POLICY, ["does_not_exist"])
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for invalid framework")


def test_crosswalk_in_result():
    engine = get_engine()
    result = engine.analyze(GOOD_POLICY, ["eu_ai_act", "iso_42001", "nist_ai_rmf"])
    assert result.crosswalk
    themes = {t.theme_id for t in result.crosswalk}
    assert "risk_management" in themes
