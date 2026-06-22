#!/usr/bin/env bash
# Launch the AI Governance Tracker locally.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
exec python3 -m uvicorn app.main:app --host "$HOST" --port "$PORT" "$@"
