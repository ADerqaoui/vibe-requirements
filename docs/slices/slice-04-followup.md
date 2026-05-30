# Slice 04 — Follow-up (post-review fixes)

Continue on branch `slice-04`. Scope: fix the review findings. **No schema change, no LLM calls,
deterministic only.** Update the handoff when done.

## Tasks

### T1 — Fix: model seed must be create-only (review F1, ruling 1)
In `backend/app/seed/run.py` (`seed_models_and_settings`): for models, **insert if missing and
do nothing if the row already exists** — never reassign fields on an existing row. (Match the
settings behavior, which is already insert-only.)
- Test: seed; edit a seeded cloud model via the service (set `api_model_id`, rates, `enabled=1`);
  re-run the seed; assert the user-edited values are preserved (not reset to defaults).

### T2 — Fix: deleting a model with call logs returns 409, not 500 (review F2, ruling 2)
In `backend/app/services/model_service.py` (`delete_model`): before deleting, check whether any
`call_logs` row references this `model_id`. If so, raise a domain error that the API maps to
**409 Conflict** with a clear message (e.g. "model has call history; disable it instead").
If there are no references, delete as now. **No schema change** — this is a service-layer guard.
- Tests: insert a minimal valid `call_logs` row referencing a model, then `DELETE /api/models/{id}`
  → 409 (and the model still exists); delete an unreferenced model → 204.

### T3 — Fix: settings PUT allowlists only the four core keys (review F3 + design concern 2, ruling 3)
In `backend/app/schemas/setting.py` / `backend/app/services/setting_service.py`: replace the
secret-name blocklist with an **allowlist**. Normalize each incoming key (strip whitespace), and
accept only: `fx_rate_usd_sek`, `complexity_tier_map`, `router_default`, `cost_ceiling_sek`.
Reject any other key (including secret-shaped or case/whitespace variants) with **422**. This both
closes the secret-injection path and scopes settings to the four known non-secret keys.
- Tests: `OPENAI_API_KEY`, `openai_api_key ` (trailing space), and an arbitrary key like `foo`
  → 422 and nothing written to the DB; the four valid keys → 200 and persisted.

### T4 — Test: exact seed set (review F4)
In `backend/tests/test_models.py`: assert the exact `(provider, name, tier, enabled)` set after
seeding equals the slice-04 seed list (six enabled Ollama models + three disabled cloud
placeholders), not just counts/flags.

## Out of scope
F5 (SettingsPanel split) is deferred to the router/selection slice. No schema changes, no new
endpoints, no gateway/LLM behavior.

## Acceptance
- `pytest` and `pnpm test` pass, including the new tests for T1–T4.
- Re-running `python -m app.seed.run` never alters a user-edited model row.
- `DELETE` on a model with call logs → 409 (controlled), without logs → 204.
- Settings PUT accepts only the four core keys; everything else → 422, nothing persisted.
- Update the handoff in `docs/exchange/slice-04.md` under "## Codex — handoff & notes",
  prefixed `[Codex — YYYY-MM-DD]`. Append only — never recreate the file.

## Constraints
- No schema/migration change. Do not read `.env` values. Do not edit constitution docs.
- One branch (`slice-04`), update the existing PR, no self-merge.
