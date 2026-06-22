from pathlib import Path

from app.ingest import (
    detect_profile,
    generate_template_from_text,
    parse_eu_html,
    parse_sections,
)
from app.frameworks import _parse_framework

FIXTURE = Path(__file__).parent / "fixtures" / "mini_standard.txt"
EU_HTML = Path(__file__).parent / "fixtures" / "mini_eurlex.html"
NIST_TEXT = """
GOVERN 1.1: Legal and regulatory requirements involving AI are understood,
managed and documented across the organisation.

GOVERN 1.2: The characteristics of trustworthy AI are integrated into
organisational policies, processes and procedures.

MAP 1.1: Intended purposes, potentially beneficial uses and context-specific
laws are understood and documented for the AI system.

MEASURE 2.1: Test sets, metrics and details about the tools used are documented
so that AI system performance and trustworthiness can be evaluated.
"""


def test_detect_profile_eu():
    text = FIXTURE.read_text()
    assert detect_profile("eu_ai_act.pdf", text) == "eu_ai_act"


def test_detect_profile_nist():
    assert detect_profile("nist_rmf.pdf", NIST_TEXT) == "nist"


def test_parse_eu_sections():
    text = FIXTURE.read_text()
    sections = parse_sections(text, "eu_ai_act")
    refs = [s.reference for s in sections]
    assert "Article 9" in refs
    assert "Article 14" in refs
    risk = next(s for s in sections if s.reference == "Article 9")
    assert "risk management" in (risk.title + risk.body).lower()


def test_parse_nist_sections():
    sections = parse_sections(NIST_TEXT, "nist")
    refs = [s.reference for s in sections]
    assert "GOVERN 1.1" in refs
    assert "MEASURE 2.1" in refs


def test_eu_postprocess_drops_inline_references():
    # An inline cross-reference (as found in recitals) followed by the real
    # article heading further down. The fragment 'of the Charter...' must be
    # dropped and only the real 'Risk management system' kept.
    text = (
        "Article 9\n"
        "of the Charter of Fundamental Rights and the protection of natural "
        "persons, which is referenced widely throughout the recitals here.\n\n"
        "Article 9\n"
        "Risk management system\n"
        "1. A risk management system shall be established, implemented and "
        "maintained for high-risk AI systems throughout their lifecycle.\n"
    )
    sections = parse_sections(text, "eu_ai_act")
    art9 = [s for s in sections if s.reference == "Article 9"]
    assert len(art9) == 1
    assert art9[0].title == "Risk management system"


def test_parse_eu_html_structured():
    html = EU_HTML.read_text()
    sections = parse_eu_html(html)
    refs = {s.reference: s for s in sections}
    assert "Article 9" in refs
    assert "Article 10" in refs
    # Stray backtick in the title must be stripped.
    assert refs["Article 9"].title == "Risk management system"
    # The annex content must not leak into Article 10's body.
    assert "annex content must not" not in refs["Article 10"].body.lower()


def test_eu_html_extraction():
    from app.extraction import extract_text

    text = extract_text("mini_eurlex.html", EU_HTML.read_bytes())
    assert "risk management system" in text.lower()
    assert "<p" not in text  # tags stripped


def test_generate_template_is_loadable():
    text = FIXTURE.read_text()
    framework, profile, n = generate_template_from_text(
        text,
        framework_id="eu_ai_act_gen",
        name="EU AI Act (generated)",
        profile="auto",
        control_prefix="EUAIA",
        filename="eu_ai_act.pdf",
    )
    assert profile == "eu_ai_act"
    assert n >= 3
    # Each control must have an id, title and keywords.
    for c in framework["controls"]:
        assert c["id"]
        assert c["title"]
        assert c["keywords"]
    # The generated dict must parse with the engine's framework loader.
    fw = _parse_framework(framework)
    assert len(fw.controls) == n
    assert fw.control_by_id(framework["controls"][0]["id"]) is not None


def test_generated_template_works_with_engine():
    from app.engine import TfidfEngine
    from app import frameworks as fw_module

    text = FIXTURE.read_text()
    framework, _, _ = generate_template_from_text(
        text,
        framework_id="eu_ai_act_gen",
        name="EU AI Act (generated)",
        filename="eu_ai_act.pdf",
    )
    fw = _parse_framework(framework)

    # Inject the generated framework into a fresh engine instance.
    engine = TfidfEngine()
    engine.frameworks = {fw.id: fw}
    policy = (
        "We maintain a risk management system and data governance with bias "
        "examination, and our systems include human oversight so operators can "
        "override or stop them."
    )
    result = engine.analyze(policy, [fw.id])
    assert result.frameworks[0].total_controls == len(fw.controls)
    # A policy that addresses all three articles should not register as all gaps.
    assert (result.summary.covered + result.summary.partial) >= 2
    assert result.frameworks[0].compliance_score > 0
