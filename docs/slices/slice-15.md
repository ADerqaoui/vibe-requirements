# Slice 15 — Cost-ceiling enforcement + cost panel

Branch: `slice-15` (from `main`). Scope: make the existing `settings.cost_ceiling_sek` value actually enforce, and give the user visibility on spend via a read-only Cost panel in Settings. **Schema-free** — `call_logs.cost_sek` and `created_at` already exist; `settings.cost_ceiling_sek` already exists (slice 04).

## In scope
1. **Spend window**: spend is measured as **current calendar month** in UTC: `SELECT COALESCE(SUM(cost_sek), 0) FROM call_logs WHERE status = 'success' AND created_at >= '<YYYY-MM-01T00:00:00>'`. Failed calls don't count (no charge).

2. **Pre-call gate** in `gateway_service.complete_model` (and any other path that triggers paid model calls — embedding service too):
   - If the target model's `input_cost_per_1k > 0 OR output_cost_per_1k > 0` (i.e., paid model) **and** the current-month spent ≥ `settings.cost_ceiling_sek`: raise a new typed `CostCeilingExceededError(spent_sek, ceiling_sek)` **before** any HTTP call to the provider; do not log a call_logs row; do not retry.
   - If the model is free (Ollama rates = 0): always proceed regardless of spend. Free calls must remain available so the user isn't locked out of the app.
   - If ceiling is `0`: every paid call is blocked (intended); free calls still work.
   - Race tolerance: the gate is a soft pre-check. A call already in flight when ceiling is reached may slightly overshoot — acceptable for a single-user dev tool. Do not add locking.

3. **API error path**: routes that catch `CostCeilingExceededError` return **HTTP 402** with body `{ "error": "cost_ceiling_exceeded", "spent_sek": <float>, "ceiling_sek": <float>, "currency": "SEK" }`. The error message in the response should be human-readable and stable enough for the frontend to detect.

4. **Cost summary endpoint**: `GET /api/cost-summary` returns
```json
   {
     "currency": "SEK",
     "ceiling_sek": 50.0,
     "month_spent_sek": 12.34,
     "month_remaining_sek": 37.66,
     "all_time_spent_sek": 18.21,
     "by_provider": [{ "provider": "anthropic", "month_sek": 8.10 }, ...],
     "by_model":    [{ "model_id": 7, "model_name": "claude-sonnet-4", "month_sek": 8.10 }, ...]
   }
```
   Sums are over `status='success'` only. `month_*` filters by current calendar month UTC. `month_remaining_sek = max(0, ceiling_sek - month_spent_sek)`. Excludes models with zero cost (no need to show "0.00 SEK on ollama").

5. **Frontend Cost panel** (read-only) inside Settings:
   - New `frontend/src/components/CostPanel.tsx` fetches `/api/cost-summary` on mount and exposes a `refresh()` callback. Display: a clear "X.XX / Y.YY SEK this month" header with a simple progress bar (or just a percentage), a small breakdown by provider, all-time total, and an inline note if ceiling is reached.
   - Integrated into the existing Settings panel above or below the model list.

6. **Frontend ceiling-exceeded surface**:
   - Extend the API client so 402 with `error: "cost_ceiling_exceeded"` parses to a typed JS error (e.g., `CostCeilingError` with `spent_sek` + `ceiling_sek`).
   - In `GenerationPanel`, catch this distinct error in the generate/accept-auto-classify paths and render a non-blocking inline banner: "Cost ceiling reached — X.XX / Y.YY SEK this month. Raise it in Settings or use a local model." The candidate list (if already on screen) is unchanged; the banner appears in place of the generation result. Free models continue to work in the same panel without triggering the banner.
   - The Inspector (slice 10) and the Classification trigger (slice 07/11 auto-classify) should at minimum surface a non-blocking error message when 402 returns; do not silently swallow. Reuse the same parsing.

7. **CostPanel refresh trigger**: after every successful generation, call `CostPanel.refresh()` so the spent counter moves in near-real-time. Pass a refresh callback from Settings to wherever it's needed, or trigger a refresh event when generation succeeds (use whatever pattern is already established in the codebase — don't introduce a new state library).

8. **Tests** (deterministic):
   - Service: paid model with spend < ceiling → proceeds normally. Paid model with spend ≥ ceiling → raises `CostCeilingExceededError`, no HTTP attempt, no `call_logs` row written. Free model (rates = 0) with spend ≥ ceiling → proceeds normally. Ceiling = 0 → blocks every paid call but allows free calls. Failed historical call (status='failure') does NOT count toward spend.
   - API: `POST /api/models/{id}/complete` returns 402 with the documented body when ceiling exceeded for a paid model; same path returns 200 for a free model regardless of ceiling.
   - Cost-summary endpoint: aggregations match a deterministic seed (e.g., two providers × two models × mix of success/failure rows in current vs prior month). `month_remaining_sek` floors at 0 when overspent. `by_provider` and `by_model` exclude zero-cost models.
   - Frontend: CostPanel renders correct numbers from a mocked summary; CostPanel.refresh re-fetches. GenerationPanel: on a mocked 402, renders the ceiling banner with the spent + ceiling values; on a 200 generation, calls CostPanel refresh.

## Out of scope (build NO behavior)
Soft warning at 80% (defer to UX polish), email/notification alerts, auto-reset on month rollover (the SQL window already handles this — no scheduled job needed), per-user budgets (single-user tool), multi-currency / FX live conversion (everything stays in SEK), forecast / projected month-end spend, paying users / Stripe, retroactive cost ceiling per-model.

## API shapes
- `GET /api/cost-summary` (new, schema above).
- `POST /api/models/{id}/complete`: behavior unchanged on success; on ceiling-block, returns 402 with `{ error, spent_sek, ceiling_sek, currency }`.
- Generation, classification, and inspection endpoints surface 402 the same way when their underlying gateway call is blocked.
- No schema migration. No new tables.

## Suggested file layout (one entity per file, ≤200 lines)
Backend: `app/services/cost_service.py` (new — computes month spend, summary, ceiling check); the typed `CostCeilingExceededError` in the existing gateway-errors module (don't create a new module just for one class); `app/api/cost.py` (new — the summary route); updated `app/services/gateway_service.py` and `app/services/embedding_service.py` to call the ceiling check before the adapter call; updated route handlers to map the typed error to 402. Tests: `test_cost_service.py`, `test_cost_api.py`, additions to `test_gateway_service.py` + `test_gateway_api.py` + `test_embedding_service.py` for the new gate.
Frontend: `frontend/src/components/CostPanel.tsx`, `frontend/src/api/cost.ts`, small extension to the API client error parser for 402, and minimal changes to GenerationPanel + the Inspector trigger. Tests: `CostPanel.test.tsx` + additions to `GenerationPanel.test.tsx`.

## Acceptance criteria
- Setting `cost_ceiling_sek` to a value below current month spend immediately blocks paid model calls with HTTP 402 + structured body, while free local models still complete normally.
- Cost panel in Settings shows current-month spend, remaining vs ceiling, all-time spend, and breakdown by provider/model.
- Successful paid generation increments the displayed cost without a page reload (CostPanel refresh).
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-15.md` with acceptance-to-test mapping.

## Constraints
- No schema changes. No new currency. No live FX. The ceiling check is a single SQL aggregate plus a numeric comparison — keep it under ~30 lines in `cost_service`. Do not pre-emptively cache the spend value (the table is tiny and the operation runs once per paid call). One branch, one PR, no self-merge.
