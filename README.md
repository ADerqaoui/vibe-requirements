# Requirement Review Dashboard

Single-user, LAN-hosted tool to generate, inspect, and export engineering
requirements with local (Ollama) and cloud LLMs.
Full spec in `requirements.md` and `architecture.md`.

## Setup

### 1. Secrets
    cp .env.example .env
    # edit .env — add cloud API keys only if you want cloud providers (optional)

### 2. Backend
    cd backend
    python -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
    alembic upgrade head
    python -m app.seed.run      # idempotent reference data seed
    uvicorn app.main:app --reload --port 8000

### 3. Frontend (second terminal)
    cd frontend
    pnpm install
    pnpm dev                    # serves on 5173

### 4. Open
- In VS Code, forward ports 8000 and 5173 to your laptop.
- Open http://localhost:5173 — the page shows backend / DB / Ollama health.

## Deployment (later slice)
`docker-compose.yml` builds backend + frontend and serves on 8080.
Ollama stays on the host (not containerized).
