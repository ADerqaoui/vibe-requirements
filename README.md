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

## Dev smoke: manual Ollama completion

Dev-only, not CI. With the backend running and an enabled Ollama model id:

    curl -X POST http://localhost:8000/api/models/<model_id>/complete \
      -H "Content-Type: application/json" \
      -d '{"prompt":"Reply with exactly: ok"}'

## Dev smoke: manual cloud completion

Dev-only, not CI. Add the relevant provider key to `.env`, start the backend,
enable the cloud model in Settings, then call the existing completion endpoint.
Cloud models remain disabled until explicitly enabled.

Anthropic:

    curl -X POST http://localhost:8000/api/models/<anthropic_model_id>/complete \
      -H "Content-Type: application/json" \
      -d '{"prompt":"Reply with exactly: ok"}'

OpenAI:

    curl -X POST http://localhost:8000/api/models/<openai_model_id>/complete \
      -H "Content-Type: application/json" \
      -d '{"prompt":"Reply with exactly: ok"}'

Deepseek:

    curl -X POST http://localhost:8000/api/models/<deepseek_model_id>/complete \
      -H "Content-Type: application/json" \
      -d '{"prompt":"Reply with exactly: ok"}'

## Deployment (later slice)
`docker-compose.yml` builds backend + frontend and serves on 8080.
Ollama stays on the host (not containerized).
