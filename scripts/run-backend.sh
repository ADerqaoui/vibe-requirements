#!/usr/bin/env bash
# Start the backend on http://127.0.0.1:8000 (idempotent DB setup + seed).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/backend"
source .venv/bin/activate
# The FastAPI startup lifespan applies migrations and seed data.
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
