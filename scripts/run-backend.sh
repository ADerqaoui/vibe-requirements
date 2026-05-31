#!/usr/bin/env bash
# Start the backend on http://127.0.0.1:8000 (idempotent DB setup + seed).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/backend"
source .venv/bin/activate
# Fresh DB -> migrate; existing-with-tables -> stamp; up-to-date -> no-op
alembic upgrade head 2>/dev/null || alembic stamp head
python -m app.seed.run
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
