# Slice 04 — Model Registry + Settings + Cost

Branch: `slice-04` (from `main`, after slice-03 is merged).
Scope: the deterministic groundwork for LLM calls — manage models, manage settings, and
compute/log cost. **No actual LLM calls, no network, no adapters** (that's slice 05).
Everything here is testable without Ollama, cloud keys, or the network.

## In scope
1. **Model registry seed** (REQ-ROUTER-005). Idempotent seed of the `models` table (already
   exists from slice 02). Seed the installed local models (cost 0) enabled, and cloud models
   as **disabled placeholders** (enabled=0; rates 0 until the User sets them):
   - ollama (tier, cost 0): `qwen2.5:7b` (mid), `llama3.1:8b` (mid), `gemma2:9b` (mid), `phi3:mini` (low), `qwen2.5-coder:7b` (mid), `mistral` (low)
   - cloud placeholders (enabled=0): anthropic `claude` (high), openai `gpt` (high), deepseek `deepseek-chat` (mid) — `api_model_id` left for the User to set with real ids/rates.
2. **Models CRUD API** (architecture.md §API):
   - `GET /api/models` — list models + each model's cumulative cost (summed from `call_logs`; 0 for now).
   - `POST /api/models` — add `{provider, name, ollama_tag?|api_model_id?, tier, input_cost_per_1k?, output_cost_per_1k?, enabled?}`.
   - `PATCH /api/models/{id}` — edit / enable / disable.
   - `DELETE /api/models/{id}` — remove (404 if missing).
3. **Settings** (key/value `settings` table; REQ-ROUTER-018, REQ-COST-005, REQ-ROUTER-006):
   - `GET /api/settings` — all settings; **API-key status is derived from `.env` and returned masked** (`configured` / `not_configured` per provider) — keys are NEVER read into the response or stored in the DB.
   - `PUT /api/settings` — update settings.
   - Seed core settings: `fx_rate_usd_sek` (default 11.0), `complexity_tier_map` (default `1-2:low,3:mid,4-5:high`), `router_default` (default `off`), `cost_ceiling_sek` (default 50).
4. **Cost computation** (REQ-COST-001..005). Pure function:
   `compute_cost_sek(in_tokens, out_tokens, input_rate_usd, output_rate_usd, fx_rate, provider) -> float`
   - `(in*input_rate + out*output_rate)/1000 * fx_rate`; **`provider == 'ollama'` (local) → 0**.
   - The function takes explicit rates (so historical cost can be frozen later by the caller).
5. **Frontend** — a Settings/Models panel: list models (tier, cost, enable/disable toggle, add/remove), show each provider's key status (configured/not), edit `fx_rate_usd_sek`, `complexity_tier_map`, `router_default`, `cost_ceiling_sek`.
6. **Tests** (deterministic, no network): models CRUD incl. enable/disable + 404; settings GET masks key status and PUT never writes a key to the DB; **cost computation property tests** — never negative, local provider → 0, correct formula, and changing a model's stored rate does not change a previously computed value (frozen-by-caller).

## Out of scope (build NO behavior)
LLM calls / gateway / adapters (slice 05), auto-routing (later), generation, classification,
inspector, the cost-ceiling enforcement modal (the ceiling *value* is stored here; enforcement
is slice 10), prompt-registry behavior.

## API shapes
- `Model`: `{ id, provider, name, ollama_tag, api_model_id, tier, input_cost_per_1k, output_cost_per_1k, enabled, cumulative_cost_sek }`.
- `Setting`: `{ key, value }`. `GET /api/settings` returns `{ settings: [...], provider_keys: { anthropic: "configured"|"not_configured", openai: ..., deepseek: ... } }`.

## Suggested file layout (one entity/function per file, ≤200 lines)
Backend: `app/seed/models_seed.py` (extend the seed runner), `app/schemas/model.py`, `app/schemas/setting.py`, `app/services/model_service.py`, `app/services/setting_service.py`, `app/services/cost.py` (pure cost fn), `app/api/models.py`, `app/api/settings.py` (register routers), `tests/test_models.py`, `tests/test_settings.py`, `tests/test_cost.py`.
Frontend: `src/types/model.ts`, `src/types/setting.ts`, `src/api/models.ts`, `src/api/settings.ts`, `src/components/SettingsPanel.tsx`, wire into `App.tsx`, `SettingsPanel.test.tsx`.

## Acceptance criteria
- Seed is idempotent: re-running yields the same model rows (local enabled, cloud disabled) and the four core settings.
- Models CRUD works incl. enable/disable; DELETE/PATCH on missing id → 404.
- `GET /api/settings` reports provider key status as configured/not_configured (masked) and reflects `.env`; no key value ever appears in the response or the DB. `PUT /api/settings` updates non-key settings only.
- `compute_cost_sek`: local → 0; cloud → correct SEK; property tests pass (non-negative, formula, frozen-by-caller).
- Frontend: list/add/enable/disable/remove models; edit the four settings; key status visible.
- `pytest` + `pnpm test` pass.
- Handoff in `docs/exchange/slice-04.md` under "## Codex — handoff & notes", prefixed `[Codex — YYYY-MM-DD]`.

## Constraints
- Do not modify the schema/migration. Do not read `.env` values into responses or the DB (only presence/absence). Do not edit constitution docs. One branch, one PR, no self-merge.
