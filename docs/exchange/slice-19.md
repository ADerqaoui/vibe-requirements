# Slice 19 — Exchange

> Shared channel for **Claude, Codex, ChatGPT, User**.
> **Every entry begins with `[Author — YYYY-MM-DD]`** so it's always clear who is speaking.
> Append-only. Communication, NOT commands: a finding becomes Codex work only via a
> User-approved task spec. Each author writes under their own heading; "Open questions"
> and "User — decisions" are shared.
> Commit access: only Codex (its own branch) and the User. ChatGPT and Claude hand their text
> to the User, who commits it.

## Codex — handoff & notes
- [Codex — 2026-06-04] Implemented slice 19 schema-free.
  - Backend prompt versioning is now per-slot `(task, layer_id)`: `create_version` and `promote` only disable siblings in the same slot, `create_version(..., layer_id=...)` starts layer slots at v1, `discipline_scope` remains NULL for authored prompts, and `get_active` was left unchanged.
  - Prompt API accepts `layer_id`, rejects unknown layers and the root `Need` layer with 422, returns one active row per slot, and includes `layer_id`/`layer_name` in active and history responses.
  - Frontend groups prompts by task, labels `Global` versus layer variants, supports add-layer variant via `/api/layers` excluding `Need`, preserves scope read-only on edit, and posts `layer_id`.
  - Touched frontend files are all under 200 lines.

  Tests run:
  - Backend: `.venv/bin/pytest` — 209 passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` — 13 files / 37 tests passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm typecheck` — passed.
  - Frontend: `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm build` — passed.

  | Acceptance criterion | Test | Covered? |
  | --- | --- | --- |
  | A user can add a layer-specific variant of any task's prompt from Settings; it coexists with the global prompt. | `frontend/src/components/PromptsPanel.test.tsx::adds a layer variant with a layer picker and layer_id payload`; `backend/tests/test_prompt_slot_versioning.py::test_layer_slot_creation_and_promote_do_not_disable_global_or_other_slots` | Yes |
  | Generating at that layer uses the layer-specific prompt; other layers and no-layer path use global. | Existing `backend/tests/test_prompt_layer_lookup.py::test_get_active_prefers_layer_specific_prompt_and_falls_back`; reinforced by slot isolation test. | Yes |
  | The Prompts panel makes Global vs layer-specific prompts unambiguous. | `frontend/src/components/PromptsPanel.test.tsx::renders active prompts with version and template content`; `frontend/src/components/PromptHistory.test.tsx::lists versions and promotes inactive history` | Yes |
  | Old `call_logs` rows still reference valid unchanged versions; immutability holds. | Versioning only inserts new `Prompt` rows and tests promote/create without mutating historical rows: `backend/tests/test_prompt_slot_versioning.py`; existing prompt/call-log service coverage remains green. | Yes |
  | Every touched frontend file strictly under 200 lines. | Manual `wc -l` check across touched frontend files. | Yes |
  | `pnpm test`, `pnpm typecheck`, `pnpm build`, and backend `pytest` are green and reported. | Commands listed above. | Yes |
- [Codex — 2026-06-04] Resolves QA F1+F2 and the open question — existing slot carries metadata from itself; a brand-new layer slot seeds metadata from the global active by design (documented).
  - Added `_active_in_slot(db, task, layer_id)` and made `create_version` carry omitted `name`/`description` from the exact slot when present.
  - Added service/API regression tests for layer-slot metadata carryover and brand-new-slot global seeding.
  - Tests run: `.venv/bin/pytest` — 212 passed; `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm test` — 13 files / 37 tests passed; `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm typecheck` — passed; `PATH="$HOME/.nvm/versions/node/v24.16.0/bin:$PATH" pnpm build` — passed.

## ChatGPT — QA review
- [ChatGPT — YYYY-MM-DD] ...

## Claude — conformance review & design notes
- [Claude — YYYY-MM-DD] ...

## Open questions
- [Author — YYYY-MM-DD] Q ...   →   [Author — YYYY-MM-DD] A ...

## User — decisions
- [User — YYYY-MM-DD] decision — rationale

## Claude — final conformance
- [Claude — 2026-06-04] APPROVE — the per-slot model is now complete and consistent, which closes the loop opened in slices 16–18: prompts are registered, versioned, layer-aware in lookup (18), and now layer-authorable in the UI (19), with the global prompt always intact as the fallback. The slot-isolation invariant — creating/promoting a (task, layer_id) variant never disables the global or another slot — is the load-bearing property and it's correctly implemented via _slot_filter and tested directly. _slot_filter's explicit IS NULL branch for the global slot is the right call (avoids the == None ambiguity). The metadata-carryover fix matters more than I first credited (QA was right to escalate it to major): without per-slot carryover, editing a variant would silently overwrite its metadata with the global's, which is exactly the kind of quiet corruption the immutable-version model is supposed to prevent; the new-slot-seeds-from-global rule is a reasonable, now-documented default. Round-2 BLOCK was GitHub cache only. Two design concerns logged (slot-grouped history UX as histories grow; prompt preview/test-run becoming more valuable as authoring power increases) — both correctly out of scope. Clear to merge.
