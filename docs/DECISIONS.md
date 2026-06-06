# Decision Log

One line per non-trivial decision: date — decision — rationale.

- 2026-05-29 — Stack: React+TS / FastAPI / SQLite+sqlite-vec / Docker Compose; Ollama on host.
- 2026-05-29 — API keys in `.env` only, never in DB or backups. (Public repo.)
- 2026-05-29 — Revision history: editing an accepted spec preserves the old version and archives inspection runs.
- 2026-05-29 — DB integrity: FK pragma per connection, STRICT tables, two-column blacklist parent + CHECK.
- 2026-05-29 — Classifier trio = qwen2.5:7b, llama3.1:8b, gemma2:9b (all local).
- 2026-05-29 — Embedding model = nomic-embed-text (local).
- 2026-05-29 — App port = 8080 in deployment (80 is taken).
- 2026-05-30 — Multi-agent workflow: Claude architect, Codex implementer, ChatGPT QA, user final decision maker. Repo is source of truth.
- [2026-06-06] Pre-V1 placeholder tables from 0001 (the abandoned disciplines/spec_disciplines/inspection_findings/spec_revisions scaffold) may be replaced forward-only by the slice that needs the name, rather than by editing historical migrations. 0004 replaces the placeholder spec_revisions. Full dead-schema cleanup is deferred to the V1 code-quality review.
