# Conventions

## Security
- Secrets (API keys) live ONLY in `.env`. Never commit `.env`. Never store keys in the DB or in backups.
- `.gitignore` excludes `.env`, `*.db`, `*.sqlite`, `*.sql`, `.venv/`, `node_modules/`.
- A `gitleaks` pre-commit scan should block any key-shaped string (added in a later step).
- Backup dumps (`/api/backup`) contain project data — keep private; never commit or share publicly.

## File size
- Default: one function per file. Closely related functions may share a file.
- Target <= 200 lines per file. Hard limit 300 lines -> split by responsibility.

## Code style (from coding-standards)
- Descriptive names; verb-noun for functions.
- Immutability by default (spread; no in-place mutation).
- Early returns over deep nesting. No magic numbers — use named constants.
- Comprehensive error handling. Functions <= ~50 lines.
- No `any` in TypeScript. Tests follow Arrange-Act-Assert.

## Ports (this server)
- 80   : taken by another container (docker-proxy) — do not use.
- 8000 : backend dev (uvicorn).
- 5173 : frontend dev (vite).
- 8080 : app entry in deployment (docker-compose).
