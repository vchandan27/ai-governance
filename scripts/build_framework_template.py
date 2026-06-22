#!/usr/bin/env python3
"""Generate a framework mapping template from a standard's PDF/DOCX/TXT.

Usage:
    python -m scripts.build_framework_template SOURCE.pdf \\
        --id eu_ai_act --name "EU AI Act" --short "EU AI Act" \\
        --version "Regulation (EU) 2024/1689" \\
        --url https://eur-lex.europa.eu/eli/reg/2024/1689/oj \\
        --profile auto --prefix EUAIA --out app/data/frameworks_local/eu_ai_act.yaml

If --out is omitted, the YAML is printed to stdout. By default templates are
written to app/data/frameworks_local/ which is git-ignored (so you don't commit
text derived from copyrighted standards). The running app will automatically
load frameworks from that directory.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running both as "python -m scripts.x" and "python scripts/x.py".
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

from app import config  # noqa: E402
from app.extraction import ExtractionError  # noqa: E402
from app.ingest import generate_template_from_document  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("source", help="Path to the standard document (.pdf/.docx/.txt/.md)")
    p.add_argument("--id", required=True, help="Framework id, e.g. eu_ai_act")
    p.add_argument("--name", required=True, help="Display name")
    p.add_argument("--short", default="", help="Short name for tables")
    p.add_argument("--version", default="", help="Version / citation")
    p.add_argument("--url", default="", help="Reference URL")
    p.add_argument("--authority", default="", help="Issuing authority")
    p.add_argument(
        "--profile",
        default="auto",
        choices=["auto", "eu_ai_act", "iso", "nist", "generic"],
        help="Structural parser to use (default: auto-detect)",
    )
    p.add_argument("--prefix", default="", help="Control id prefix, e.g. EUAIA")
    p.add_argument(
        "--out",
        default="",
        help="Output YAML path (default: app/data/frameworks_local/<id>.yaml)",
    )
    p.add_argument("--stdout", action="store_true", help="Print YAML instead of writing a file")
    args = p.parse_args()

    src = Path(args.source)
    if not src.exists():
        print(f"error: source not found: {src}", file=sys.stderr)
        return 2

    try:
        framework, profile_used, n = generate_template_from_document(
            src.read_bytes(),
            filename=src.name,
            framework_id=args.id,
            name=args.name,
            short_name=args.short,
            version=args.version,
            reference_url=args.url,
            profile=args.profile,
            control_prefix=args.prefix,
            authority=args.authority,
        )
    except ExtractionError as exc:
        print(f"error: could not read document: {exc}", file=sys.stderr)
        return 2

    yaml_text = yaml.safe_dump(framework, sort_keys=False, allow_unicode=True, width=100)

    print(
        f"Parsed '{src.name}' with profile '{profile_used}': extracted {n} candidate controls.",
        file=sys.stderr,
    )
    if n == 0:
        print(
            "warning: no controls detected. Try a different --profile, or the PDF "
            "may be scanned (no selectable text / needs OCR).",
            file=sys.stderr,
        )

    if args.stdout:
        print(yaml_text)
        return 0

    out = Path(args.out) if args.out else (config.LOCAL_FRAMEWORKS_DIR / f"{args.id}.yaml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml_text, encoding="utf-8")
    print(f"Wrote template -> {out}", file=sys.stderr)
    print(
        "Review the draft (titles, descriptions, keywords, weights) before relying on it. "
        "The app will load it automatically from frameworks_local/.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
