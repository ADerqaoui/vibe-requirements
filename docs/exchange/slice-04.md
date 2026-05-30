# Slice 04 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions" and
> "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — YYYY-MM-DD] ...
- [Codex — 2026-05-30] Implemented slice 04 deterministic Model Registry + Settings + Cost. Added idempotent model/settings seed for local Ollama models, disabled cloud placeholders, and the four slice settings. Added Models CRUD API with cumulative `call_logs` cost, Settings API with masked provider key statuses only, pure `compute_cost_sek`, and deterministic backend coverage for seed idempotence, model CRUD/404s, settings masking/secret rejection, and cost properties. Added frontend Settings/Models panel for listing, adding, enabling/disabling, removing models, editing slice settings, and showing provider key status. Tests run: `cd backend && .venv/bin/pytest` (23 passed), `cd frontend && PATH=/home/aiserver/.nvm/versions/node/v24.16.0/bin:$PATH pnpm test` (6 passed), and `cd frontend && PATH=/home/aiserver/.nvm/versions/node/v24.16.0/bin:$PATH pnpm build` (passed). Deviations: none for scope; no schema/migration changes and no LLM calls/adapters.
- [Codex — 2026-05-30] Implemented follow-up T1-T4 exactly. T1: model seed now inserts missing seed rows only and preserves user-edited existing model rows. T2: deleting a model with `call_logs` now returns 409 with "model has call history; disable it instead"; unreferenced deletes still return 204. T3: Settings PUT now strips incoming keys and accepts only `fx_rate_usd_sek`, `complexity_tier_map`, `router_default`, and `cost_ceiling_sek`; secret-shaped and arbitrary keys return 422 without DB writes. T4: model seed tests now assert the exact seeded `(provider, name, tier, enabled)` set. Tests run: `cd backend && .venv/bin/pytest` (28 passed), `cd frontend && PATH=/home/aiserver/.nvm/versions/node/v24.16.0/bin:$PATH pnpm test` (6 passed). Deviations: none; no schema changes, no LLM calls, and `.env` was not read.

## ChatGPT — QA review
-  [ChatGPT — 2026-05-30] Verdict: BLOCK.

  Findings:

  1. Category: Bug
     Severity: major
     Location: `backend/app/seed/run.py` — `seed_models_and_settings`
     What's wrong and why it matters: The model seed updates existing seeded model rows back to the seed defaults every time the seed runner is executed. That means if the User later edits a seeded cloud placeholder with a real `api_model_id`, rates, tier, or enabled state, running `python -m app.seed.run` again will overwrite those values back to the defaults. Slice 04 says cloud placeholders have rates 0 "until the User sets them"; the current seed behavior can erase those user-set values. This is especially risky because the seed command is part of normal setup/dev workflow.
     Suggested check or fix: Add a test that seeds, edits a seeded cloud model's `api_model_id`, rates, and enabled flag, runs the seed again, and verifies the user-edited values are preserved. The seed should create missing rows but should not clobber user-managed model configuration after first creation, unless there is an explicit reset operation.

  2. Category: Bug
     Severity: major
     Location: `backend/app/services/model_service.py` — `delete_model`; `backend/app/api/models.py` — `delete_model_route`
     What's wrong and why it matters: `call_logs.model_id` has a foreign key to `models.id`, but no `ON DELETE SET NULL` / cascade behavior. The Models API supports `DELETE /api/models/{id}`. If a model has any call-log rows, deleting it will likely raise a database integrity error and return an unsafe 500 instead of a controlled API response. This matters because the same slice exposes cumulative model cost from `call_logs`, so models with historical logs are expected.
     Suggested check or fix: Add a backend test that inserts a `call_logs` row for a model and then attempts to delete that model. The API should return a controlled response rather than an unhandled 500. The desired behavior is a policy decision: either reject deletion with a clear conflict response, soft-disable instead, or preserve audit by nulling/retaining references if the architecture allows it.

  3. Category: Security
     Severity: major
     Location: `backend/app/schemas/setting.py` — `SettingsUpdate.reject_secret_settings`; `backend/app/services/setting_service.py` — `update_settings`
     What's wrong and why it matters: Settings PUT rejects only exact keys `anthropic_api_key`, `openai_api_key`, and `deepseek_api_key`. It does not normalize setting keys before checking, and it allows arbitrary new settings to be inserted. A request using a key like `openai_api_key `, `OPENAI_API_KEY`, or another key-shaped secret name could still persist secret material into the DB. Slice 04 explicitly requires API keys to never be stored in the DB and says PUT updates non-key settings only.
     Suggested check or fix: Add tests for key normalization / secret-like variants and arbitrary setting insertion. The API should accept only the allowed non-secret settings for this slice: `fx_rate_usd_sek`, `complexity_tier_map`, `router_default`, and `cost_ceiling_sek`, unless the architect explicitly approves arbitrary settings.

  4. Category: Missing test
     Severity: minor
     Location: `backend/tests/test_models.py` — `test_seed_models_and_settings_is_idempotent`
     What's wrong and why it matters: The seed test verifies counts/provider enabled states, but it does not verify the exact seeded model set from the slice: the six specific Ollama models and three disabled cloud placeholders with the expected tiers. A wrong model name or tier could pass if provider counts and enabled flags still look correct.
     Suggested check or fix: Compare the exact `(provider, name, tier, enabled)` set against the slice seed list.

  5. Category: Risk
     Severity: minor
     Location: `frontend/src/components/SettingsPanel.tsx`
     What's wrong and why it matters: `SettingsPanel.tsx` is 224 lines, above the project convention target of 200 lines though below the hard 300-line limit. It already handles settings loading, model creation, toggling, deletion, settings editing, key-status display, and rendering in one component. This is acceptable for this slice, but it is likely to grow when router/model selection behavior is added.
     Suggested check or fix: No immediate blocker by itself. Consider splitting later into smaller pieces such as `ModelList`, `ModelForm`, `SettingsForm`, and `ProviderKeyStatus`.

  Things that look fine:

  * The PR is now a clean Slice 04 delta against current `main`; no stacked Slice 03/Slice 02 pollution is visible in the compare.
  * No schema or Alembic migration files appear in the clean Slice 04 delta.
  * No LLM gateway/adapters/network behavior appears to be added.
  * Settings GET exposes provider key status only as configured/not_configured and the tests check that literal secret values do not appear in the response.
  * The pure cost function covers local provider cost as zero, cloud formula, non-negative valid cases, negative-input rejection, and caller-frozen rates.
  * Frontend test coverage exists for listing models/settings/key status, adding a model, toggling enable state, removing a model, and saving settings.
  * I did not see `.env`, database dumps, SQLite files, SQL dumps, or committed secret material in the reviewed Slice 04 delta.

  Design concerns for the architect:

  1. Model deletion semantics need a clear policy before call logs become real audit records. Hard-delete conflicts with preserving cost/audit history unless the schema or API explicitly defines how historical `call_logs.model_id` should behave.
  2. Settings API scope should be clarified: either this slice only allows the four core settings, or arbitrary non-secret settings are intentionally allowed. The current implementation allows arbitrary setting keys, which may be broader than the slice text.

  Open questions:

  * [ChatGPT — 2026-05-30] For the User/Claude: Should seeded model rows be protected from being overwritten after the User edits them?
  * [ChatGPT — 2026-05-30] For the User/Claude: Should deleting a model with historical call logs be rejected, converted to disable-only, or allowed with an explicit audit-preserving DB rule?


## Claude — conformance review & design notes
- [Claude — 2026-05-30] BLOCK — concur with ChatGPT; verified all three majors. F1: model seed overwrites existing rows each run (clobbers user-edited cloud models); settings are correctly insert-only, models aren't. F2: delete_model has no guard; call_logs.model_id FK (no ON DELETE) → deleting a referenced model raises IntegrityError → 500. F3: settings PUT blocklists 3 exact key names and upserts arbitrary keys → a secret-shaped variant could persist to the DB. Rulings: (1) model seed create-only; (2) DELETE model → 409 if call_logs reference it (disable instead), no schema change; (3) settings PUT allowlists exactly the 4 core keys, reject others 422. F4 fold in (exact seed-set test); F5 defer SettingsPanel split.

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale
