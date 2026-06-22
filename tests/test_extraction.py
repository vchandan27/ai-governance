import pytest

from app.extraction import ExtractionError, extract_text, segment_text


def test_extract_txt():
    text = extract_text("policy.txt", b"Hello world. This is a policy.")
    assert "policy" in text.lower()


def test_extract_md():
    text = extract_text("policy.md", b"# Heading\n\nSome governance content here.")
    assert "governance" in text.lower()


def test_unsupported_extension():
    with pytest.raises(ExtractionError):
        extract_text("policy.exe", b"data")


def test_empty_file():
    with pytest.raises(ExtractionError):
        extract_text("policy.txt", b"   \n  ")


def test_segment_text_splits_paragraphs():
    text = (
        "This is the first paragraph about governance and accountability.\n\n"
        "This is a second paragraph discussing risk management practices."
    )
    segments = segment_text(text)
    assert len(segments) == 2


def test_segment_text_drops_short_fragments():
    text = "ok\n\nThis is a sufficiently long governance paragraph for analysis."
    segments = segment_text(text)
    assert all(len(s) >= 25 for s in segments)
