"""The mapping engine: maps policy text onto framework controls.

The default engine is dependency-light and fully offline. It blends two signals:

1. **Semantic similarity** - TF-IDF vectors with cosine similarity between each
   control's descriptive text and each segment of the uploaded policy. This
   captures paraphrased coverage even when exact keywords differ.
2. **Keyword coverage** - the fraction of a control's curated keywords that
   appear in the document. This grounds the score in domain terminology.

The two are blended into a 0..1 score and classified as covered / partial / gap
using per-framework thresholds. The design is deliberately pluggable so a future
LLM- or embedding-based engine can be swapped in (see ``ROADMAP``).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import config
from .extraction import segment_text
from .frameworks import (
    Control,
    Framework,
    load_crosswalk,
    load_frameworks,
)
from .schemas import (
    AnalysisResponse,
    AnalysisSummary,
    ControlResult,
    CoverageStatus,
    CrosswalkThemeResult,
    Evidence,
    FrameworkResult,
)

# Weight between semantic similarity and keyword coverage in the blended score.
SEMANTIC_WEIGHT = 0.5
KEYWORD_WEIGHT = 0.5

_TOKEN_RE = re.compile(r"[a-z][a-z\-]+")


def _light_stem(token: str) -> str:
    """A tiny, dependency-free stemmer to fold common English inflections.

    It is deliberately conservative (handles the suffixes that matter most for
    governance vocabulary: monitoring/monitored -> monitor, incidents ->
    incident, etc.) so we keep the engine free of heavy NLP dependencies.
    """
    for suffix in ("ization", "isation", "ements", "ement", " ation", "ations",
                   "ings", "ing", "ied", "ies", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            token = token[: -len(suffix)]
            break
    return token.rstrip("-")


def _stem_analyzer(text: str) -> list[str]:
    tokens = []
    for raw in _TOKEN_RE.findall(text.lower()):
        if raw in ENGLISH_STOP_WORDS or len(raw) < 2:
            continue
        tokens.append(_light_stem(raw))
    # add adjacent bigrams of stems for a little phrase sensitivity
    bigrams = [f"{a} {b}" for a, b in zip(tokens, tokens[1:])]
    return tokens + bigrams


_STATUS_VALUE = {
    CoverageStatus.COVERED: 1.0,
    CoverageStatus.PARTIAL: 0.5,
    CoverageStatus.GAP: 0.0,
}
_STATUS_RANK = {CoverageStatus.GAP: 0, CoverageStatus.PARTIAL: 1, CoverageStatus.COVERED: 2}


@dataclass
class _Match:
    score: float
    semantic: float
    keyword_ratio: float
    matched_keywords: list[str]
    evidence: list[Evidence]


class TfidfEngine:
    """Default offline mapping engine."""

    name = "tfidf-keyword-v1"

    def __init__(self) -> None:
        self.frameworks = load_frameworks()
        self.crosswalk = load_crosswalk()

    # -- keyword matching -------------------------------------------------
    @staticmethod
    def _stem_tokens(text: str) -> list[str]:
        return [_light_stem(t) for t in _TOKEN_RE.findall(text.lower())]

    @classmethod
    def _find_keywords(cls, keywords: list[str], doc_stems: set[str]) -> list[str]:
        """Return keywords whose stemmed tokens are all present in the document.

        Stemming lets a curated keyword like "monitoring" match "monitored" in
        the policy. Multi-word keywords require every (non-trivial) token to be
        present, which keeps precise phrases (e.g. "post-market monitoring")
        from matching loosely.
        """
        found = []
        for kw in keywords:
            kw_stems = [s for s in cls._stem_tokens(kw) if len(s) >= 2]
            if not kw_stems:
                continue
            if all(s in doc_stems for s in kw_stems):
                found.append(kw)
        return found

    # -- core analysis ----------------------------------------------------
    def analyze(self, text: str, framework_ids: list[str]) -> AnalysisResponse:
        selected = [self.frameworks[fid] for fid in framework_ids if fid in self.frameworks]
        if not selected:
            raise ValueError("No valid frameworks selected.")

        segments = segment_text(text)
        if not segments:
            segments = [text]

        doc_stems = set(self._stem_tokens(text))

        # Build a shared TF-IDF space over segments + all control queries.
        all_controls: list[tuple[Framework, Control]] = [
            (fw, c) for fw in selected for c in fw.controls
        ]
        control_queries = [c.query_text for _, c in all_controls]
        corpus = segments + control_queries

        vectorizer = TfidfVectorizer(
            analyzer=_stem_analyzer,
            sublinear_tf=True,
            min_df=1,
        )
        matrix = vectorizer.fit_transform(corpus)
        seg_matrix = matrix[: len(segments)]
        query_matrix = matrix[len(segments):]

        # cosine similarity: (n_controls x n_segments)
        sims = cosine_similarity(query_matrix, seg_matrix)

        matches: dict[str, _Match] = {}
        for idx, (_fw, control) in enumerate(all_controls):
            matches[f"{_fw.id}:{control.id}"] = self._score_control(
                control, sims[idx], segments, doc_stems
            )

        framework_results: list[FrameworkResult] = []
        all_control_results: list[ControlResult] = []
        for fw in selected:
            fw_result = self._build_framework_result(fw, matches)
            framework_results.append(fw_result)
            all_control_results.extend(fw_result.controls)

        summary = self._build_summary(framework_results, all_control_results)
        crosswalk = self._build_crosswalk(selected, matches)

        return AnalysisResponse(
            document_name="",  # filled by caller
            document_chars=len(text),
            segments_analyzed=len(segments),
            engine=self.name,
            summary=summary,
            frameworks=framework_results,
            crosswalk=crosswalk,
        )

    def _score_control(
        self, control: Control, sim_row, segments: list[str], doc_stems: set[str]
    ) -> _Match:
        matched_keywords = self._find_keywords(control.keywords, doc_stems)
        keyword_ratio = (
            len(matched_keywords) / len(control.keywords) if control.keywords else 0.0
        )

        # Top evidence segments by similarity.
        ranked = sorted(
            range(len(segments)), key=lambda i: sim_row[i], reverse=True
        )
        evidence: list[Evidence] = []
        for i in ranked[: config.MAX_EVIDENCE_PER_CONTROL]:
            sim = float(sim_row[i])
            if sim < config.MIN_EVIDENCE_SIMILARITY:
                break
            seg = segments[i]
            seg_kw = self._find_keywords(control.keywords, set(self._stem_tokens(seg)))
            evidence.append(
                Evidence(
                    text=seg[:500],
                    similarity=round(sim, 3),
                    matched_keywords=seg_kw,
                )
            )

        semantic = float(sim_row[ranked[0]]) if len(ranked) else 0.0
        # Scale semantic: TF-IDF cosine rarely exceeds ~0.6 for relevant matches.
        semantic_scaled = min(1.0, semantic / 0.6)
        score = SEMANTIC_WEIGHT * semantic_scaled + KEYWORD_WEIGHT * keyword_ratio
        return _Match(
            score=round(score, 4),
            semantic=round(semantic, 4),
            keyword_ratio=round(keyword_ratio, 4),
            matched_keywords=matched_keywords,
            evidence=evidence,
        )

    def _classify(self, fw: Framework, score: float) -> CoverageStatus:
        if score >= fw.covered_threshold:
            return CoverageStatus.COVERED
        if score >= fw.partial_threshold:
            return CoverageStatus.PARTIAL
        return CoverageStatus.GAP

    def _recommendation(
        self, control: Control, status: CoverageStatus
    ) -> str | None:
        if status == CoverageStatus.COVERED:
            return None
        expected = " ".join(control.expected_evidence).strip()
        if status == CoverageStatus.PARTIAL:
            lead = (
                f"Partial coverage of '{control.title}' ({control.reference}). "
                "Some related language was found but it does not fully address "
                "the requirement. Strengthen the policy by explicitly covering: "
            )
        else:
            lead = (
                f"Gap: no clear evidence for '{control.title}' "
                f"({control.reference}). Add a policy section addressing: "
            )
        return (lead + (expected or control.description)).strip()

    def _build_framework_result(
        self, fw: Framework, matches: dict[str, _Match]
    ) -> FrameworkResult:
        control_results: list[ControlResult] = []
        weighted_sum = 0.0
        weight_total = 0
        covered = partial = gaps = 0
        for control in fw.controls:
            m = matches[f"{fw.id}:{control.id}"]
            status = self._classify(fw, m.score)
            if status == CoverageStatus.COVERED:
                covered += 1
            elif status == CoverageStatus.PARTIAL:
                partial += 1
            else:
                gaps += 1
            weighted_sum += control.weight * _STATUS_VALUE[status]
            weight_total += control.weight
            control_results.append(
                ControlResult(
                    control_id=control.id,
                    title=control.title,
                    reference=control.reference,
                    category=control.category,
                    weight=control.weight,
                    status=status,
                    score=m.score,
                    evidence=m.evidence,
                    matched_keywords=m.matched_keywords,
                    recommendation=self._recommendation(control, status),
                    description=control.description,
                )
            )
        compliance = (weighted_sum / weight_total * 100) if weight_total else 0.0
        return FrameworkResult(
            framework_id=fw.id,
            name=fw.name,
            short_name=fw.short_name,
            version=fw.version,
            reference_url=fw.reference_url,
            compliance_score=round(compliance, 1),
            covered=covered,
            partial=partial,
            gaps=gaps,
            total_controls=len(fw.controls),
            controls=control_results,
        )

    def _build_summary(
        self,
        framework_results: list[FrameworkResult],
        all_controls: list[ControlResult],
    ) -> AnalysisSummary:
        covered = sum(1 for c in all_controls if c.status == CoverageStatus.COVERED)
        partial = sum(1 for c in all_controls if c.status == CoverageStatus.PARTIAL)
        gaps = sum(1 for c in all_controls if c.status == CoverageStatus.GAP)
        # Overall score: mean of framework compliance scores (equal framework weight).
        overall = (
            sum(f.compliance_score for f in framework_results) / len(framework_results)
            if framework_results
            else 0.0
        )
        # Top gaps: highest-weight gap/partial controls first.
        ranked_gaps = sorted(
            [c for c in all_controls if c.status != CoverageStatus.COVERED],
            key=lambda c: (_STATUS_RANK[c.status], -c.weight, c.score),
        )
        return AnalysisSummary(
            overall_score=round(overall, 1),
            total_controls=len(all_controls),
            covered=covered,
            partial=partial,
            gaps=gaps,
            top_gaps=ranked_gaps[:8],
        )

    def _build_crosswalk(
        self, selected: list[Framework], matches: dict[str, _Match]
    ) -> list[CrosswalkThemeResult]:
        selected_ids = {fw.id for fw in selected}
        fw_by_id = {fw.id: fw for fw in selected}
        results: list[CrosswalkThemeResult] = []
        for theme in self.crosswalk:
            statuses: dict[str, CoverageStatus | None] = {}
            best_rank = -1
            best_status: CoverageStatus | None = None
            relevant = False
            for fid, control_ids in theme.controls.items():
                if fid not in selected_ids:
                    continue
                if not control_ids:
                    statuses[fid] = None
                    continue
                relevant = True
                fw = fw_by_id[fid]
                theme_best: CoverageStatus | None = None
                theme_best_rank = -1
                for cid in control_ids:
                    m = matches.get(f"{fid}:{cid}")
                    if m is None:
                        continue
                    status = self._classify(fw, m.score)
                    if _STATUS_RANK[status] > theme_best_rank:
                        theme_best_rank = _STATUS_RANK[status]
                        theme_best = status
                statuses[fid] = theme_best
                if theme_best is not None and _STATUS_RANK[theme_best] > best_rank:
                    best_rank = _STATUS_RANK[theme_best]
                    best_status = theme_best
            if not relevant:
                continue
            results.append(
                CrosswalkThemeResult(
                    theme_id=theme.id,
                    title=theme.title,
                    statuses=statuses,
                    overall_status=best_status or CoverageStatus.GAP,
                )
            )
        return results


_ENGINE: TfidfEngine | None = None


def get_engine() -> TfidfEngine:
    """Return a process-wide engine instance (frameworks are cached)."""
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = TfidfEngine()
    return _ENGINE
