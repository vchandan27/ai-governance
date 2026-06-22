# AI Governance Tracker

Draft browser-based workspace for mapping an organization AI policy to common AI
governance profiles:

- EU AI Act
- ISO/IEC 42001
- NIST AI Risk Management Framework
- OECD AI Principles

The current version is intentionally dependency-free and runs as static HTML,
CSS, and JavaScript.

## Run locally

Open `index.html` in a browser, or serve the folder with any static file server:

```bash
python3 -m http.server 8000
```

Then visit <http://localhost:8000>.

## Test

```bash
npm test
```

## What the draft does

1. Accepts pasted policy text or uploaded text-like files (`.txt`, `.md`,
   `.csv`, `.json`, `.html`, `.xml`).
2. Maps policy language to governance profile dimensions.
3. Shows profile scores, matched control areas, evidence snippets, and priority
   gaps.
4. Exports a JSON report for downstream review.
5. Documents improvement angles for policy intelligence, framework depth,
   enterprise workflow, and assurance.

## Draft limitations

- This is not legal, compliance, or certification advice.
- The scoring engine is keyword/evidence based and should be used as first-pass
  triage only.
- PDF and Word parsing are not included; export those documents to text before
  upload.
- Framework profiles are summarized and should be expanded into citation-level
  controls before production use.

## Product improvement roadmap

- Replace keyword matching with clause extraction, semantic embeddings, and
  confidence scoring.
- Add framework citations, obligation triggers, jurisdiction applicability, and
  evidence requirements.
- Add model inventory integration, owner assignment, remediation plans,
  approvals, exceptions, audit logs, and issue tracking.
- Add reviewer override workflows so compliance teams can accept, reject, or
  annotate AI-generated mappings.
- Add role-based access control, encryption, data retention policies, and
  privacy-preserving processing for sensitive policy documents.
- Generate auditor-ready evidence packs with source citations and change
  history.
