#!/usr/bin/env bash
# Start the backend on http://127.0.0.1:8000 with safe DB setup.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/backend"
source .venv/bin/activate

# Apply migrations; show the real error if any. Fall back to stamp only when the
# DB has the existing-tables-but-no-alembic_version condition (first-time-stamp).
if ! alembic upgrade head; then
  if alembic current 2>/dev/null | grep -q "^$"; then
    echo "Alembic version not stamped — stamping existing DB to head and retrying."
    alembic stamp head
    alembic upgrade head
  else
    echo "Alembic upgrade failed — see the trace above." >&2
    exit 1
  fi
fi

python -m app.seed.run
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
