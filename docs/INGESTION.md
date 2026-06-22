# Generating mapping templates from official standard PDFs

You can turn the **source documents** of a standard or regulation (EU AI Act,
ISO/IEC 42001, NIST AI RMF, or any other) into a **mapping template** — a set of
controls in the same YAML schema the engine uses — and then run a policy against
it. This is a two-step workflow:

```
standard PDF ──▶ build_framework_template ──▶ framework template (YAML)
                                                     │
policy PDF ───────────────▶ analyze_cli ◀────────────┘
                                  │
                                  ▼
                    coverage report (covered / partial / gap + evidence)
```

## Step 1 — build a template from the standard

```bash
# EU AI Act
python -m scripts.build_framework_template /path/to/eu_ai_act.pdf \
    --id eu_ai_act --name "EU AI Act" --short "EU AI Act" \
    --version "Regulation (EU) 2024/1689" \
    --url https://eur-lex.europa.eu/eli/reg/2024/1689/oj \
    --profile eu_ai_act --prefix EUAIA

# ISO/IEC 42001
python -m scripts.build_framework_template /path/to/iso_42001.pdf \
    --id iso_42001 --name "ISO/IEC 42001:2023" --short "ISO 42001" \
    --version "2023" --profile iso --prefix ISO

# NIST AI RMF
python -m scripts.build_framework_template /path/to/nist_ai_rmf.pdf \
    --id nist_ai_rmf --name "NIST AI RMF 1.0" --short "NIST AI RMF" \
    --version "1.0" --profile nist --prefix NIST
```

By default each template is written to `app/data/frameworks_local/<id>.yaml`,
which is **git-ignored** (see "Copyright" below) and is loaded automatically by
the app and the CLI. Pass `--out PATH` to write elsewhere, or `--stdout` to print.

If you use the same `id` as a curated framework, the generated template
**overrides** the curated one — so you can replace the hand-written EU AI Act
controls with ones extracted from the official text.

### Parser profiles

The `--profile` flag selects how the document is split into controls:

| Profile | Detects | Good for |
| --- | --- | --- |
| `eu_ai_act` | `Article N` + the title line that follows | EU AI Act / EU regulations |
| `iso` | numbered clauses (`6.1.2 …`) and Annex A controls (`A.6.2.4 …`) | ISO/IEC standards |
| `nist` | `GOVERN/MAP/MEASURE/MANAGE N.N` subcategories | NIST AI RMF / Playbook |
| `generic` | numbered headings (`1.2.3 Title`) | other structured documents |
| `auto` (default) | picks the best profile by filename + content | unsure |

The tool prints how many controls it extracted. **Always review the draft** —
titles, descriptions, keywords and `weight` — before relying on it. Automated
parsing of legal/standards PDFs is approximate, and scanned (image-only) PDFs
need OCR first (not included in this draft).

## Step 2 — check a policy against the template(s)

```bash
# Plain-text summary in the terminal
python -m scripts.analyze_cli /path/to/company_policy.pdf --frameworks all

# A specific set, exported as Markdown
python -m scripts.analyze_cli /path/to/company_policy.pdf \
    --frameworks eu_ai_act,iso_42001 --format markdown --out report.md

# Machine-readable JSON
python -m scripts.analyze_cli /path/to/company_policy.pdf --format json --out report.json
```

You can also use the web UI / REST API exactly as before — generated frameworks
appear automatically in `GET /api/frameworks` and in the framework picker.

## Tuning quality

- **Keywords** are auto-derived (TF-IDF over the extracted controls). Edit them in
  the YAML to add domain synonyms your policies actually use — this is the single
  biggest lever on recall.
- **Weights** (1–5) drive the weighted compliance score; raise them for the
  controls that matter most to you.
- **Thresholds** per framework (`covered`, `partial`) control how strict the
  classification is.
- For deeper accuracy (semantic understanding, negation handling, LLM-as-judge),
  see [`ROADMAP.md`](ROADMAP.md). The engine is pluggable behind `get_engine()`.

## Copyright / licensing note

EU legislation (the AI Act) is publicly available and reproducible. **ISO/IEC
standards are copyrighted** — you may parse a copy you have licensed for your own
internal use, but do **not** commit text derived from them to a public repo. That
is why generated templates default to the git-ignored `frameworks_local/`
directory. Treat generated descriptions as internal working notes.
