# Slice 12 — Blacklist (semantic dedup of rejected statements)

Branch: `slice-12` (from `main`). Scope: when a generation candidate is **Rejected**, persist it to the existing `blacklist_entries` table (per-parent, `source='rejected'`) AND compute its 768-dim embedding via Ollama `nomic-embed-text` into the existing `blacklist_vec` (sqlite-vec virtual table). On the next Generate against the same parent, filter LLM candidates whose cosine similarity ≥ 0.85 against any of that parent's blacklist entries. **Schema-free** — `blacklist_entries` + `blacklist_vec` already exist from 0001. Hardcoded threshold (0.85) and embedding model (`nomic-embed-text`); both become settings in a later slice.

## In scope
1. **Embedding service** — `app/services/embedding_service.py`: `embed(text) -> list[float]` (768 dims). Hits Ollama `POST /api/embeddings` with `model: nomic-embed-text` (looked up by `ollama_tag` from the registry; must be `enabled=True`; raises a clear error if missing/disabled). Uses the same resilience pattern as the slice-05 gateway (retry + timeout, settings-driven). Dependency-injectable so tests use a fake.
2. **Blacklist service** — `app/services/blacklist_service.py`:
   - `add_blacklist_entry(parent_kind, parent_id, statement)` — inserts a row in `blacklist_entries` with `source='rejected'`, embeds via the embedding service, inserts the vector in `blacklist_vec` (entry_id ↔ blacklist_entries.id). Transactional: both rows, or neither (rollback the entry on embed failure).
   - `list_entries(parent_kind, parent_id)` — returns entries (no embeddings in the response).
   - `filter_against_blacklist(parent_kind, parent_id, candidates) -> list[str]` — embeds each candidate, queries `blacklist_vec` for the parent's entries, computes cosine similarity, returns the subset with **max cosine < 0.85**. Empty blacklist → unchanged.
3. **Generation integration** — `generation_service.generate_for_parent` calls `filter_against_blacklist` after parsing, before returning. The API response shape stays the same (`{candidates: [...]}`); the frontend simply receives fewer/zero candidates after filtering.
4. **API**:
   - `POST /api/needs/{need_id}/blacklist` `{statement: str}` → 201 `BlacklistEntryOut`. 404 missing Need; 422 blank statement; 502 if the embedding call fails (no row written — transactional).
   - `POST /api/specs/{spec_id}/blacklist` — analogous, 404 missing Spec.
   - `GET /api/needs/{need_id}/blacklist` and `GET /api/specs/{spec_id}/blacklist` → list scoped to that parent, newest-first.
5. **Frontend** — extend the Reject handler in `GenerationCandidates.tsx` (or wherever it lives post-slice-11 split): in addition to removing the candidate from the UI, POST to the parent's blacklist endpoint with the rejected statement. Best-effort: on failure, `console.warn` and continue (Reject still removes the candidate from view). Show a small "Blacklist: N" counter near each parent in the tree-owning component; refresh after Reject. If a Generate response returns zero candidates, show "All candidates were blocked by the blacklist — try again or rephrase."
6. **Tests** (deterministic, no live network):
   - Embedding service: fake HTTP returns a known 768-dim vector; correct parsing; clear error if model missing/disabled; retry/timeout behavior matches the slice-05 pattern.
   - Blacklist service: `add` writes both `blacklist_entries` and `blacklist_vec`; `list` filters by parent; **cross-parent isolation** (entries under Need 1 don't appear for Need 2 or under any Spec); embed failure → rollback (no orphan entry).
   - Filter: with fakes returning controlled embeddings (one candidate close, one far), the close one is filtered out and the far one survives; threshold boundary (cosine = 0.849 keeps, 0.851 drops); empty blacklist passes everything through.
   - Generation integration: a parent with a Reject already recorded receives a Generate request → response excludes semantically-close candidates (proven with pre-computed embedding pairs).
   - API: 201 on create with `BlacklistEntryOut`; 404 missing parent; 422 blank statement; 502 on embed failure with no row written; GET returns newest-first, scoped.
   - Frontend: Reject calls the blacklist endpoint with the rejected statement; counter increments and refreshes; zero-candidates UI message appears when generation returns empty after filtering.

## Out of scope (build NO behavior)
UI to view/remove/edit blacklist entries (later "blacklist manager" slice); cross-parent blacklist propagation (strictly per-parent); re-embedding when the embedding model changes; `source='edited_out'` (only `rejected` this slice); settings-driven embedding model or threshold (hardcode `nomic-embed-text` and `0.85`); auto-blacklist of low-quality inspector findings; cost-ceiling on embedding calls (local = 0); Router ON; cloud-side embedding adapters.

## API shapes
- `BlacklistCreate`: `{ statement: str }`.
- `BlacklistEntryOut`: `{ id, parent_need_id?, parent_spec_id?, text, source, created_at }`.

## Suggested file layout (one entity/function per file, ≤200 lines; keep the embedding path injectable)
Backend: `app/services/embedding_service.py`, `app/services/blacklist_service.py`, `app/schemas/blacklist.py`, `app/api/blacklist.py` (register router). Modify `app/services/generation_service.py` to call `filter_against_blacklist` post-parse. Tests: `test_embedding_service.py`, `test_blacklist_service.py`, `test_blacklist_api.py`, extend `test_generation_service.py` with the filter integration.
Frontend: `src/api/blacklist.ts`, `src/types/blacklist.ts`. Extend the Reject handler in `GenerationCandidates.tsx`; add a "Blacklist: N" counter on the parent in the tree-owning component; "all blocked" empty-state message. Component tests.

## Acceptance criteria
- Rejecting a candidate POSTs to the parent's blacklist endpoint; the entry persists in `blacklist_entries` and the embedding persists in `blacklist_vec` (atomic — neither without the other).
- A subsequent Generate on the same parent excludes candidates with cosine ≥ 0.85 to any of that parent's blacklist entries.
- Cross-parent isolation: blacklisting under Need A doesn't affect Need B or under any Spec.
- If filtering drops everything, the API returns an empty `candidates` list and the frontend shows a clear "all blocked" message.
- API: 201 create, 404 missing parent, 422 blank, 502 on embed failure (no row written); GET scoped + newest-first.
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-12.md` with an acceptance-to-test mapping.

## Constraints
- No schema changes (`blacklist_entries` + `blacklist_vec` exist from 0001). Embedding service is separate from the chat gateway (different endpoint, different concerns), but follows the same resilience + injectable pattern. Threshold (0.85) and embedding model (`nomic-embed-text`) are hardcoded constants for this slice; settings-driven values are a later slice. Use a transactional write for entry+vector (rollback on embed failure). One branch, one PR, no self-merge.
