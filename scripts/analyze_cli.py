#!/usr/bin/env python3
"""Run a compliance check of a policy document against governance frameworks.

Usage:
    python -m scripts.analyze_cli POLICY.pdf --frameworks all
    python -m scripts.analyze_cli POLICY.md --frameworks eu_ai_act,iso_42001 \\
        --format markdown --out report.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engine import get_engine  # noqa: E402
from app.extraction import ExtractionError, extract_text  # noqa: E402
from app.frameworks import load_frameworks  # noqa: E402
from app.reporting import to_markdown  # noqa: E402
from app.schemas import CoverageStatus  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("policy", help="Path to the policy document (.pdf/.docx/.txt/.md)")
    p.add_argument("--frameworks", default="all", help="Comma-separated ids or 'all'")
    p.add_argument("--format", default="text", choices=["text", "markdown", "json"])
    p.add_argument("--out", default="", help="Write output to a file instead of stdout")
    args = p.parse_args()

    available = list(load_frameworks().keys())
    if args.frameworks.strip().lower() in ("", "all"):
        ids = available
    else:
        ids = [f.strip() for f in args.frameworks.split(",") if f.strip()]
        unknown = [f for f in ids if f not in available]
        if unknown:
            print(f"error: unknown framework(s): {', '.join(unknown)}. "
                  f"Available: {', '.join(available)}", file=sys.stderr)
            return 2

    src = Path(args.policy)
    if not src.exists():
        print(f"error: policy not found: {src}", file=sys.stderr)
        return 2
    try:
        text = extract_text(src.name, src.read_bytes())
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = get_engine().analyze(text, ids)
    result.document_name = src.name

    if args.format == "json":
        output = result.model_dump_json(indent=2)
    elif args.format == "markdown":
        output = to_markdown(result)
    else:
        output = _render_text(result)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Wrote report -> {args.out}", file=sys.stderr)
    else:
        print(output)
    return 0


def _render_text(result) -> str:
    icon = {CoverageStatus.COVERED: "[x]", CoverageStatus.PARTIAL: "[~]", CoverageStatus.GAP: "[ ]"}
    s = result.summary
    lines = [
        f"AI Governance compliance check: {result.document_name}",
        f"Overall coverage: {s.overall_score}/100  "
        f"(covered {s.covered} / partial {s.partial} / gaps {s.gaps} of {s.total_controls})",
        "",
    ]
    for fw in result.frameworks:
        lines.append(
            f"== {fw.name}  {fw.compliance_score}/100  "
            f"(cov {fw.covered}/part {fw.partial}/gap {fw.gaps})"
        )
        for c in fw.controls:
            lines.append(f"  {icon[c.status]} {c.score:>4.2f}  {c.reference:<22} {c.title}")
        lines.append("")
    if s.top_gaps:
        lines.append("Priority gaps:")
        for c in s.top_gaps:
            lines.append(f"  - [{c.status.value}] {c.title} ({c.reference})")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
