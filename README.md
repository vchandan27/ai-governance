# AI Governance Tracker

Upload your organisation's AI / data / governance policy and automatically map it
against major AI governance frameworks — **EU AI Act**, **ISO/IEC 42001:2023**, and the
**NIST AI Risk Management Framework 1.0** — to see where you are **covered**, where
coverage is **partial**, and where you have **gaps**, with concrete recommendations.

> ⚖️ **Disclaimer:** This is a *draft / decision-support* tool. Automated mapping is
> not legal advice and does not constitute certification of compliance. Always have
> qualified legal, risk and compliance experts review results.

---

## What it does

1. **Ingest** a policy document (`.pdf`, `.docx`, `.txt`, `.md`) or pasted text.
2. **Segment** the document into analysable passages.
3. **Map** each passage against a curated knowledge base of framework controls using
   a hybrid engine (semantic TF-IDF similarity + stemmed keyword coverage).
4. **Classify** every control as `covered` / `partial` / `gap`, attach the supporting
   evidence passages, and generate a recommendation for anything not fully covered.
5. **Score** each framework (weighted by control importance) and produce a unified,
   framework-agnostic **cross-framework view** via a crosswalk.
6. **Export** a shareable Markdown or JSON report.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for a diagram and design notes.

---

## Quick start

```bash
# 1. Install dependencies (Python 3.10+)
pip install -r requirements.txt

# 2. Run the app
./scripts/run.sh           # or: python -m uvicorn app.main:app --reload

# 3. Open the UI
open http://localhost:8000
```

No API keys or external services are required — the default engine runs fully offline.

### Try it without a document

Open the UI, go to the **Use sample** tab, and load the bundled
`sample_policies/acme_responsible_ai_policy.md`.

---

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET`  | `/api/health` | Liveness probe. |
| `GET`  | `/api/frameworks` | List supported frameworks and control counts. |
| `POST` | `/api/analyze` | Analyse an uploaded file. Multipart: `file`, `frameworks`. |
| `POST` | `/api/analyze/text` | Analyse pasted text. Form: `text`, `frameworks`, `name`. |
| `POST` | `/api/report` | Download a `markdown` or `json` report. Form: `file`, `frameworks`, `fmt`. |

`frameworks` is a comma-separated list of ids (`eu_ai_act`, `iso_42001`, `nist_ai_rmf`)
or `all`. Interactive docs are available at `/docs`.

Example:

```bash
curl -F "file=@sample_policies/acme_responsible_ai_policy.md" \
     -F "frameworks=all" \
     http://localhost:8000/api/analyze | jq .summary
```

---

## How mapping works

The default engine (`tfidf-keyword-v1`) blends two signals into a 0–1 score per control:

- **Semantic similarity** — TF-IDF vectors (with a light, dependency-free stemmer and
  bigrams) and cosine similarity between each control's descriptive text and each
  policy passage. Catches paraphrased coverage.
- **Keyword coverage** — the fraction of a control's curated, stemmed keywords present
  in the document. Grounds the score in domain terminology.

`score = 0.5 · semantic + 0.5 · keyword_coverage`, then classified using per-framework
thresholds. Framework compliance is a **weighted** roll-up (each control has an
importance `weight`; `covered = 1.0`, `partial = 0.5`, `gap = 0`).

The engine is **pluggable** (`app/engine.py`) — see [`docs/ROADMAP.md`](docs/ROADMAP.md)
for the planned embedding/LLM upgrade path and why the draft stays offline by default.

---

## Generate a template from a standard's PDF, then check a policy against it

Have the official EU AI Act / ISO 42001 / NIST AI RMF PDFs? You can auto-generate a
mapping **template** from them and immediately run a policy against it:

```bash
# 1. Build a framework template from the standard's PDF
python -m scripts.build_framework_template /path/to/eu_ai_act.pdf \
    --id eu_ai_act --name "EU AI Act" --profile eu_ai_act --prefix EUAIA

# 2. Check a policy for compliance against it (terminal / Markdown / JSON)
python -m scripts.analyze_cli /path/to/company_policy.pdf --frameworks all --format markdown
```

Generated templates land in the git-ignored `app/data/frameworks_local/` (so text
derived from copyrighted standards isn't committed) and are picked up automatically by
the app, API and CLI. Automated parsing is **best-effort and meant for human review**.
Full guide: [`docs/INGESTION.md`](docs/INGESTION.md).

## Extending the knowledge base

Frameworks are declarative YAML in [`app/data/frameworks/`](app/data/frameworks). To add
a framework (e.g. ISO/IEC 23894, the OECD AI Principles, Colorado AI Act), drop in a new
`*.yaml` file following the existing schema — no code changes required. Cross-framework
relationships live in [`app/data/crosswalk.yaml`](app/data/crosswalk.yaml).

```yaml
id: my_framework
name: My Framework
short_name: MyFW
version: "1.0"
reference_url: https://example.org
thresholds: { covered: 0.32, partial: 0.14 }
controls:
  - id: MF-1
    title: Example control
    reference: Section 1
    category: Governance
    weight: 4
    description: What the control requires...
    keywords: [governance, accountability, ...]
    expected_evidence: [What good coverage looks like...]
```

---

## Project layout

```
app/
  main.py            FastAPI app + routes
  engine.py          Pluggable mapping/scoring engine (TF-IDF + keywords)
  extraction.py      PDF/DOCX/TXT/MD text extraction + segmentation
  ingest.py          Parse a standard's PDF -> framework template (controls)
  frameworks.py      YAML loader + in-memory models
  reporting.py       Markdown report renderer
  schemas.py         Pydantic API contracts
  config.py          Env-driven configuration
  data/frameworks/   EU AI Act, ISO 42001, NIST AI RMF (declarative YAML)
  data/crosswalk.yaml  Cross-framework theme mapping
  static/            Single-page UI (vanilla JS, no build step)
scripts/
  build_framework_template.py  CLI: standard PDF -> mapping template
  analyze_cli.py     CLI: check a policy against frameworks (text/md/json)
  run.sh             Launcher
docs/                Architecture, roadmap & ingestion guide
sample_policies/     Example policy to try
tests/               pytest suite (engine, extraction, ingest, API)
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Limitations (read these)

- The control set per framework is **representative, not exhaustive**, and is a
  simplified, plain-language summary of the source instruments.
- The offline engine matches *language*, not *meaning* — it can miss coverage phrased
  very differently, and can over-credit superficial keyword hits. Treat scores as a
  triage signal, not a verdict.
- Scanned/image PDFs are not OCR'd in this draft.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for how each limitation is addressed.
