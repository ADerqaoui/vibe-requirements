# Agent Operating Rules

These rules apply to any AI agent (Codex, etc.) working in this repository.

## Hard rules — never break
1. NEVER open, read, print, or copy the contents of `.env`, or any file matching
   `*.db`, `*.sqlite`, `*.sql`. You only ever need `.env.example` for structure.
2. NEVER commit secrets. The `.gitignore` and `gitleaks` pre-commit hook enforce this.
3. NEVER change scope. Build exactly what the active `docs/slices/slice-NN.md` defines.
   If something is missing or wrong, stop and note it in the PR — do not invent.
4. NEVER edit `requirements.md`, `architecture.md`, `CONVENTIONS.md`, or `docs/ROLES.md`.
   Propose changes in the PR description instead.

## Workflow
- One slice per branch, named `slice-NN`.
- Before coding, read: the active slice spec, `CONVENTIONS.md`, and the relevant part
  of `architecture.md`.
- Implement, run the tests and the app against the real stack (Ollama at
  http://localhost:11434, the venv, the DB), then write the handoff.
- Commit clearly, push the branch, open a PR. Do NOT merge your own PR.

## Coding standards (see CONVENTIONS.md)
- One function per file by default; <=200 lines/file, hard split at 300 by responsibility.
- Descriptive names; immutability; early returns; no magic numbers; full error handling;
  no `any` in TypeScript. Match existing structure in backend/app/ and frontend/src/.

## Environment
- Backend: Python 3.13, venv at backend/.venv, FastAPI, SQLAlchemy, Alembic, SQLite+sqlite-vec.
- Frontend: Node LTS, pnpm, React 18 + TypeScript + Vite + Tailwind 3.
- Ports: backend 8000, frontend 5173. Port 80 is taken — do not use.
