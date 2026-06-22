"""Turn an official standard/regulation document into a framework template.

Given the source text of a standard (e.g. the EU AI Act, ISO/IEC 42001 or the
NIST AI RMF), this module detects the structural units (articles / clauses /
subcategories), extracts a title and a short description for each, and derives
candidate keywords. The result is a framework dict in exactly the schema the
mapping engine consumes, so it can be written to YAML and used immediately.

Important: automated parsing of complex legal/standards PDFs is best-effort. The
output is a **draft template for human review**, not an authoritative encoding of
the standard. Some standards (notably ISO) are copyrighted - keep generated
templates in the git-ignored ``frameworks_local`` directory and do not commit
derived text.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from .extraction import normalize_whitespace


@dataclass
class Section:
    reference: str
    title: str
    body: str
    category: str = "General"
    control_id: str = ""
    keywords: list[str] = field(default_factory=list)


# --- structural detection profiles --------------------------------------------
# Each profile knows how to find the headings that delimit controls in a given
# family of documents. ``heading`` returns (reference, inline_title, category)
# for a matching line, or None.

_GENERIC_STOP = set(ENGLISH_STOP_WORDS) | {
    "shall", "system", "systems", "ai", "use", "used", "ensure", "including",
    "may", "article", "annex", "clause", "section", "paragraph", "point",
}


def _eu_heading(line: str):
    m = re.match(r"^\s*Article\s+(\d+)\b\s*(.*)$", line)
    if m:
        return f"Article {m.group(1)}", m.group(2).strip(), "Article"
    return None


def _nist_heading(line: str):
    m = re.match(
        r"^\s*(GOVERN|MAP|MEASURE|MANAGE)\s+(\d+(?:\.\d+)?)\b\s*[:\-]?\s*(.*)$",
        line,
        re.IGNORECASE,
    )
    if m:
        func = m.group(1).upper()
        ref = f"{func} {m.group(2)}"
        return ref, m.group(3).strip(), func.capitalize()
    return None


def _iso_heading(line: str):
    # Annex A controls, e.g. "A.6.2.4 Title"
    m = re.match(r"^\s*(A(?:\.\d+){1,4})\s+([A-Z].{2,90})$", line)
    if m:
        return m.group(1), m.group(2).strip(), "Annex A"
    # Main clauses, e.g. "6.1.2 AI risk assessment"
    m = re.match(r"^\s*(\d{1,2}(?:\.\d{1,2}){1,3})\s+([A-Z].{2,90})$", line)
    if m:
        return m.group(1), m.group(2).strip(), f"Clause {m.group(1).split('.')[0]}"
    return None


def _generic_heading(line: str):
    # Numbered headings like "1.2 Title" or "1.2.3 Title"
    m = re.match(r"^\s*(\d{1,2}(?:\.\d{1,2}){0,3})\s+([A-Z].{2,90})$", line)
    if m:
        return m.group(1), m.group(2).strip(), "Section"
    return None


PROFILES = {
    "eu_ai_act": _eu_heading,
    "nist": _nist_heading,
    "iso": _iso_heading,
    "generic": _generic_heading,
}


def detect_profile(filename: str, text: str) -> str:
    """Heuristically pick the best structural profile for a document."""
    name = (filename or "").lower()
    head = text[:8000]
    if "nist" in name or re.search(r"\b(GOVERN|MEASURE|MANAGE)\b\s+\d", head):
        return "nist"
    if "42001" in name or "iso" in name:
        return "iso"
    if "ai act" in name or "1689" in name or re.search(r"\bArticle\s+\d+\b", head):
        return "eu_ai_act"
    # Fall back based on which profile finds the most headings.
    best, best_n = "generic", 0
    for key, fn in PROFILES.items():
        n = sum(1 for ln in text.splitlines() if fn(ln))
        if n > best_n:
            best, best_n = key, n
    return best


def _make_control_id(prefix: str, reference: str, index: int) -> str:
    token = re.sub(r"[^A-Za-z0-9.]+", "-", reference).strip("-").upper()
    token = token.replace("ARTICLE-", "ART-")
    if not token:
        token = str(index)
    return f"{prefix}-{token}" if prefix else token


def parse_sections(
    text: str,
    profile: str,
    min_body: int = 40,
    max_sections: int = 400,
) -> list[Section]:
    """Split document text into candidate controls using the chosen profile."""
    heading_fn = PROFILES.get(profile, PROFILES["generic"])
    text = normalize_whitespace(text)
    lines = text.split("\n")

    sections: list[Section] = []
    current: Section | None = None
    pending_title_for: Section | None = None

    for line in lines:
        hit = heading_fn(line)
        if hit:
            ref, inline_title, category = hit
            if current and current.body.strip():
                sections.append(current)
            current = Section(reference=ref, title=inline_title, body="", category=category)
            # EU-style docs put the title on the line *after* the "Article N".
            pending_title_for = current if not inline_title else None
            continue
        if current is None:
            continue
        stripped = line.strip()
        if pending_title_for is current and stripped:
            current.title = stripped[:120]
            pending_title_for = None
            continue
        if stripped:
            current.body += (" " if current.body else "") + stripped

    if current and current.body.strip():
        sections.append(current)

    # Filter out noise (too-short bodies, table-of-contents lines, etc.).
    cleaned = [s for s in sections if len(s.body) >= min_body]

    if profile == "eu_ai_act":
        cleaned = _postprocess_eu(cleaned)

    return cleaned[:max_sections]


_LOWER_CONNECTORS = ("of ", "in ", "to ", "and ", "or ", "as ", "for ", "the ",
                     "that ", "which ", "with ", "by ", "on ", "shall ", "applies")


def _valid_eu_title(title: str) -> bool:
    """Distinguish a real article heading (e.g. 'Risk management system') from an
    inline cross-reference fragment captured from the recitals."""
    t = title.strip().strip("`").strip()
    if not (3 <= len(t) <= 100):
        return False
    if not t[0].isupper():
        return False
    if t.endswith((",", ";", ":")):
        return False
    low = t.lower()
    if any(low.startswith(c) for c in _LOWER_CONNECTORS):
        return False
    return True


def _postprocess_eu(sections: list[Section]) -> list[Section]:
    """Drop inline references and keep one (richest) section per article number,
    preserving numeric order."""
    valid = [s for s in sections if _valid_eu_title(s.title)]
    best: dict[str, Section] = {}
    for s in valid:
        s.title = s.title.strip().strip("`").strip()
        prev = best.get(s.reference)
        if prev is None or len(s.body) > len(prev.body):
            best[s.reference] = s
    return sorted(best.values(), key=lambda s: int(re.sub(r"\D", "", s.reference) or 0))


def derive_keywords(sections: list[Section], top_k: int = 8) -> None:
    """Populate each section's keywords using TF-IDF over the section corpus."""
    if not sections:
        return
    corpus = [f"{s.title} {s.body}" for s in sections]
    vectorizer = TfidfVectorizer(
        stop_words=list(_GENERIC_STOP),
        ngram_range=(1, 2),
        min_df=1,
        token_pattern=r"[A-Za-z][A-Za-z\-]{2,}",
    )
    try:
        matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        return
    vocab = vectorizer.get_feature_names_out()
    for i, section in enumerate(sections):
        row = matrix[i].toarray()[0]
        ranked = row.argsort()[::-1]
        kws: list[str] = []
        for idx in ranked:
            if row[idx] <= 0:
                break
            term = vocab[idx]
            if term in kws:
                continue
            kws.append(term)
            if len(kws) >= top_k:
                break
        # Always include salient words from the title.
        for tok in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", section.title.lower()):
            if tok not in _GENERIC_STOP and tok not in kws:
                kws.append(tok)
        section.keywords = kws[: top_k + 4]


def _short_description(body: str, max_chars: int = 360) -> str:
    body = body.strip()
    if len(body) <= max_chars:
        return body
    cut = body[:max_chars]
    last = cut.rfind(". ")
    if last > 80:
        cut = cut[: last + 1]
    return cut.strip()


def build_framework(
    *,
    framework_id: str,
    name: str,
    short_name: str,
    version: str,
    reference_url: str,
    sections: list[Section],
    control_prefix: str = "",
    default_weight: int = 3,
    authority: str = "",
) -> dict:
    """Assemble a framework dict in the engine's YAML schema."""
    controls = []
    for i, s in enumerate(sections, start=1):
        cid = s.control_id or _make_control_id(control_prefix, s.reference, i)
        title = s.title or s.reference or f"Control {i}"
        controls.append(
            {
                "id": cid,
                "title": title[:120],
                "reference": s.reference,
                "category": s.category,
                "weight": default_weight,
                "description": _short_description(s.body),
                "keywords": s.keywords or [],
                "expected_evidence": [
                    f"Policy text demonstrating '{title.strip()[:80]}'."
                ],
            }
        )
    return {
        "id": framework_id,
        "name": name,
        "short_name": short_name,
        "version": version,
        "authority": authority,
        "reference_url": reference_url,
        "description": (
            f"Template auto-generated from the source document for {name}. "
            "DRAFT - review controls, descriptions and keywords before relying on it."
        ),
        "thresholds": {"covered": 0.32, "partial": 0.14},
        "controls": controls,
    }


def generate_template_from_text(
    text: str,
    *,
    framework_id: str,
    name: str,
    short_name: str = "",
    version: str = "",
    reference_url: str = "",
    profile: str = "auto",
    control_prefix: str = "",
    filename: str = "",
) -> tuple[dict, str, int]:
    """High-level helper: text -> (framework_dict, profile_used, n_controls)."""
    used_profile = detect_profile(filename, text) if profile in ("", "auto") else profile
    sections = parse_sections(text, used_profile)
    derive_keywords(sections)
    framework = build_framework(
        framework_id=framework_id,
        name=name,
        short_name=short_name or name,
        version=version,
        reference_url=reference_url,
        sections=sections,
        control_prefix=control_prefix,
    )
    return framework, used_profile, len(sections)
