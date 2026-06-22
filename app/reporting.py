"""Render analysis results into a shareable Markdown report."""
from __future__ import annotations

from datetime import datetime, timezone

from .schemas import AnalysisResponse, CoverageStatus

_STATUS_LABEL = {
    CoverageStatus.COVERED: "Covered",
    CoverageStatus.PARTIAL: "Partial",
    CoverageStatus.GAP: "Gap",
}
_STATUS_ICON = {
    CoverageStatus.COVERED: "[x]",
    CoverageStatus.PARTIAL: "[~]",
    CoverageStatus.GAP: "[ ]",
}


def to_markdown(result: AnalysisResponse) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []
    lines.append(f"# AI Governance Coverage Report")
    lines.append("")
    lines.append(f"- **Document:** {result.document_name or 'N/A'}")
    lines.append(f"- **Generated:** {now}")
    lines.append(f"- **Engine:** {result.engine}")
    lines.append(
        f"- **Segments analysed:** {result.segments_analyzed} "
        f"({result.document_chars} characters)"
    )
    lines.append("")
    s = result.summary
    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"**Overall coverage score: {s.overall_score} / 100**")
    lines.append("")
    lines.append(
        f"- Covered: {s.covered}  |  Partial: {s.partial}  |  Gaps: {s.gaps}  "
        f"(of {s.total_controls} controls)"
    )
    lines.append("")
    lines.append("> Disclaimer: automated mapping is decision-support only and "
                 "does not constitute legal advice or a certification of compliance.")
    lines.append("")

    if s.top_gaps:
        lines.append("## Priority gaps")
        lines.append("")
        for c in s.top_gaps:
            lines.append(
                f"- **{_STATUS_LABEL[c.status]}** - {c.title} ({c.reference}) "
                f"[weight {c.weight}]"
            )
            if c.recommendation:
                lines.append(f"  - {c.recommendation}")
        lines.append("")

    for fw in result.frameworks:
        lines.append(f"## {fw.name}")
        lines.append("")
        lines.append(f"- Version: {fw.version}")
        lines.append(f"- Compliance score: **{fw.compliance_score} / 100**")
        lines.append(
            f"- Covered {fw.covered} / Partial {fw.partial} / Gaps {fw.gaps} "
            f"(of {fw.total_controls})"
        )
        lines.append(f"- Reference: {fw.reference_url}")
        lines.append("")
        lines.append("| Status | Control | Ref | Score |")
        lines.append("| --- | --- | --- | --- |")
        for c in fw.controls:
            lines.append(
                f"| {_STATUS_ICON[c.status]} {_STATUS_LABEL[c.status]} "
                f"| {c.title} | {c.reference} | {c.score:.2f} |"
            )
        lines.append("")
        # Detailed evidence/recommendations
        for c in fw.controls:
            if c.status == CoverageStatus.COVERED and not c.recommendation:
                continue
            lines.append(f"### {c.title} ({c.reference}) - {_STATUS_LABEL[c.status]}")
            if c.recommendation:
                lines.append(f"- Recommendation: {c.recommendation}")
            if c.evidence:
                lines.append("- Evidence:")
                for ev in c.evidence:
                    snippet = ev.text.replace("\n", " ").strip()
                    lines.append(f"  - ({ev.similarity:.2f}) \"{snippet}\"")
            lines.append("")

    if result.crosswalk:
        lines.append("## Cross-framework view")
        lines.append("")
        fw_ids = [fw.short_name for fw in result.frameworks]
        header = "| Theme | " + " | ".join(fw_ids) + " | Overall |"
        sep = "| --- | " + " | ".join("---" for _ in fw_ids) + " | --- |"
        lines.append(header)
        lines.append(sep)
        id_order = [fw.framework_id for fw in result.frameworks]
        for theme in result.crosswalk:
            cells = []
            for fid in id_order:
                st = theme.statuses.get(fid)
                cells.append("-" if st is None else _STATUS_LABEL[st])
            lines.append(
                f"| {theme.title} | " + " | ".join(cells) +
                f" | {_STATUS_LABEL[theme.overall_status]} |"
            )
        lines.append("")

    return "\n".join(lines)
