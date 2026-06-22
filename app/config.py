"""Application configuration.

Values are read from environment variables so the service can be configured
without code changes. Defaults are chosen so the app runs out-of-the-box with
no external dependencies or API keys.
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FRAMEWORKS_DIR = DATA_DIR / "frameworks"
# Optional second directory for locally-generated / private framework templates
# (e.g. templates derived from copyrighted standards such as ISO 42001). This
# directory is git-ignored by default so derived content is never committed.
LOCAL_FRAMEWORKS_DIR = Path(
    os.environ.get("AIGOV_EXTRA_FRAMEWORKS_DIR", str(DATA_DIR / "frameworks_local"))
)
CROSSWALK_FILE = DATA_DIR / "crosswalk.yaml"
STATIC_DIR = BASE_DIR / "static"

# Maximum upload size in bytes (default 10 MB).
MAX_UPLOAD_BYTES = int(os.environ.get("AIGOV_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))

# Maximum number of evidence snippets returned per control.
MAX_EVIDENCE_PER_CONTROL = int(os.environ.get("AIGOV_MAX_EVIDENCE", 3))

# Minimum cosine similarity for a segment to be considered as evidence.
MIN_EVIDENCE_SIMILARITY = float(os.environ.get("AIGOV_MIN_EVIDENCE_SIM", 0.08))

# Allowed upload file extensions.
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}
