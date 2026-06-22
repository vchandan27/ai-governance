# Roadmap & "all angles" — how to improve the AI Governance Tracker

This document is the product/engineering thinking behind the draft: the perspectives
that matter for a real AI governance tracker, what the draft does today, and how to
evolve it. It is organised by stakeholder and concern so trade-offs are explicit.

## 0. What the draft delivers today (baseline)

- Upload (`.pdf/.docx/.txt/.md`) or paste a policy → mapped to EU AI Act, ISO/IEC
  42001 and NIST AI RMF controls.
- Hybrid **offline** engine (TF-IDF + stemmed keyword coverage) with per-control
  `covered/partial/gap` status, **evidence passages**, **recommendations**, weighted
  **compliance scores**, a **cross-framework crosswalk**, and Markdown/JSON export.
- Declarative YAML knowledge base; pluggable engine; web UI + REST API; tests.

---

## 1. Mapping quality (the core of the product)

The biggest lever. Today's lexical engine matches *words*, not *meaning*.

- **Semantic embeddings.** Add an `EmbeddingEngine` using `sentence-transformers`
  (e.g. `all-MiniLM-L6-v2`) or an embeddings API. Store control embeddings; encode
  policy passages; rank by cosine. Far better recall for paraphrased coverage.
- **LLM-as-judge / RAG.** For each control, retrieve the top-k passages (vector search)
  and ask an LLM: *"Does this evidence satisfy requirement X? Cite the sentence; rate
  covered/partial/gap; explain."* Produces grounded, explainable verdicts and drafts
  the missing-clause text. Keep it **optional** and behind a flag because policy text
  is sensitive (see Privacy).
- **Hybrid retrieval + reranking.** BM25 + dense vectors + a cross-encoder reranker.
- **Calibration & ground truth.** Build a labelled corpus (expert-annotated policies →
  control coverage) and measure precision/recall/F1 per control; tune thresholds per
  control rather than per framework. Track confusion between partial/gap.
- **Confidence & abstention.** Surface a confidence score; when low, flag "needs human
  review" instead of guessing.
- **Negation & scope handling.** "We do **not** perform biometric categorisation" should
  not count as coverage of a prohibition the same way as an actual control. Detect
  negation, modality ("should" vs "must"), and applicability.
- **Multilingual.** EU policies arrive in many languages; use multilingual embeddings
  and/or translate-then-map.

## 2. Framework & content coverage (the moat)

- **Expand to full control sets** and exact citations (article/recital/clause/annex),
  reviewed by subject-matter experts. Version each framework.
- **More frameworks:** ISO/IEC 23894 (AI risk), ISO/IEC 5338 (AI lifecycle), OECD AI
  Principles, US Executive Orders/OMB memos, Colorado AI Act, NYC Local Law 144,
  GDPR/data-protection overlap, sectoral rules (FDA, financial model risk SR 11-7).
- **Crosswalk maturity.** Curate authoritative mappings (many bodies publish EU AI Act ↔
  ISO 42001 ↔ NIST crosswalks). "Answer once, satisfy many."
- **Content governance.** A reviewed pipeline for updating controls when regulations
  change, with provenance and effective dates.

## 3. From document mapping to a real governance system

A policy-to-framework mapper is step one. A governance *tracker* should track posture
over time across the organisation:

- **AI system inventory / use-case register** with EU AI Act **risk tiering**
  (prohibited / high / limited / minimal) and Annex III classification logic.
- **Control implementation status** distinct from *policy* coverage — a policy can
  *say* the right thing while the control isn't *operating*. Track both.
- **Evidence & artefact management:** link model cards, DPIAs/FRIAs, datasheets, test
  reports, audit logs as evidence with owners and review dates.
- **Tasks, owners, due dates, workflows** to remediate gaps; reminders for periodic
  reviews (ISO management review, post-market monitoring).
- **Continuous monitoring & drift:** re-run mapping when policies or frameworks change;
  alert on regressions; "what changed since last version" diffs.
- **Risk register** tying identified AI risks to controls and treatments.

## 4. Trust, explainability & accuracy guarantees

- Every score must be **traceable** to the exact source sentence(s) and the exact
  framework clause. (Draft already shows evidence + references.)
- Show **why** something is a gap, not just that it is. Offer suggested clause text.
- **No hallucinated citations** — if using an LLM, constrain to retrieved text and
  validate citations programmatically.
- Prominent, non-dismissable **"not legal advice"** framing and human-in-the-loop
  review before any compliance claim.

## 5. Security, privacy & data governance (we are handling sensitive docs)

- **Data residency / offline mode** for regulated customers (the default engine already
  needs no egress). LLM/embedding API calls must be opt-in and configurable to private
  endpoints; redact PII before egress.
- **AuthN/Z & multi-tenancy:** SSO/OIDC, RBAC (viewer/editor/admin/auditor), org-level
  data isolation.
- **Encryption** at rest and in transit; configurable retention and "delete my
  document"; **audit logging** of who saw/changed what.
- **Tenant isolation** for any persisted vectors/documents.
- Secrets via environment/secret manager — never in code (the app reads config from env).

## 6. Architecture & scalability

- **Persistence:** Postgres for inventory/results/audit; object storage for documents;
  a vector DB (pgvector/Qdrant/Weaviate) for embeddings.
- **Async processing:** large docs and LLM calls via a task queue (Celery/RQ/Arq) with
  progress; the API returns a job id and streams status.
- **Caching:** cache embeddings per (framework version, control) and per document hash.
- **OCR pipeline** for scanned PDFs (Tesseract/Textract); table & layout extraction.
- **Observability:** structured logs, metrics, tracing; quality dashboards (coverage
  distributions, reviewer overrides).
- **Packaging:** Dockerfile + compose; Helm chart; horizontal scaling of stateless API.

## 7. UX & reporting

- **Reviewer workflow:** accept/override a verdict, add notes; overrides become training
  data and are reflected in the score.
- **Diffs over time:** "coverage improved from 44 → 61 after policy v3".
- **Executive vs auditor views;** branded **PDF** exports; evidence appendices.
- **Inline document view** with highlighted passages mapped to controls.
- **Bulk upload** of a policy suite; per-business-unit rollups.
- Accessibility (WCAG), i18n, dark/light themes (UI is dark today).

## 8. Quality engineering & MLOps

- Golden-set regression tests for mapping; track precision/recall over releases.
- Prompt/version pinning and evaluation harness if/when LLMs are used.
- Framework-content review checklist and sign-off before publishing changes.
- Load/perf tests for large documents; fuzz tests for malformed uploads.

## 9. Business / GTM perspective

- Positioning: "answer once, satisfy many frameworks." Crosswalk is the headline value.
- Integrations: GRC tools (ServiceNow, OneTrust, Vanta), ticketing (Jira), evidence
  sources (MLflow, model registries), document stores (SharePoint, Google Drive).
- Compliance of the tool itself: it is an AI system → dogfood the governance process.
- Pricing around number of AI systems / frameworks / seats; on-prem tier for regulated.

## 10. Suggested next milestones

1. **M1 – Accuracy:** add the embedding engine + labelled eval set; tune per-control
   thresholds; add negation handling. *(highest impact)*
2. **M2 – Persistence & auth:** Postgres + object store + pgvector; SSO + RBAC;
   document/version history and coverage diffs.
3. **M3 – Governance workflow:** AI system inventory, risk tiering, evidence linking,
   remediation tasks, reviewer overrides.
4. **M4 – Optional LLM/RAG verdicts** (opt-in, private-endpoint capable) with strict
   citation validation, plus OCR and PDF report export.
5. **M5 – Expand frameworks & curated crosswalks;** integrations with GRC/ticketing.

> Guiding principle: **augment experts, don't replace them.** Optimise for explainable,
> traceable, privacy-respecting decision support — and make it trivially easy to add and
> maintain frameworks as the regulatory landscape evolves.
