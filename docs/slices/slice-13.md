# Slice 13 — Frontend hygiene (deferred F1 + F2 + F3 from slices 11/12)

Branch: `slice-13` (from `main`). Scope: a small frontend-only cleanup slice clearing three deferred minor items from slices 11 and 12. **No new features, no backend changes, no schema changes.** Behavior-preserving refactor + two regression tests + one bug fix.

## In scope
1. **F1 fix (slice-11/12 carryover) — classifying-state leak on tree-refresh failure** — in `GenerationPanel.tsx::handleAccept`, the new Spec id is added to `classifyingSpecIds`, then `loadSpecTree(effectiveRootNeedId)` is awaited. If that refresh throws, control jumps to the outer `catch` and the id is never removed → permanent "Classifying…" indicator if the Spec later appears in the tree. Fix: wrap the post-create work so the classifying id is **always** removed (try/finally pattern, or restructure so the id is added immediately before the classify call and a finally block removes it on either path). The classify call should still run even if the tree-refresh fails — they're independent concerns.

2. **F2 fix (slice-12 missing test) — blacklist POST failure path** — in `GenerationPanel.test.tsx::handleReject`, add a test:
   - Render with a parent and a candidate present.
   - Mock the blacklist API POST to reject (e.g., 500 or network error).
   - Trigger Reject.
   - Assert: the candidate is removed from the rendered list; no blocking error UI appears; `console.warn` is called once with a recognizable message (the slice-12 implementation chose its own warning string — assert it begins with "Blacklist" or whatever it actually uses).

3. **F3 fix (slice-12 size) — split `GenerationPanel.tsx` under 200 lines** — currently 241 lines. Extract one or more of the following so `GenerationPanel.tsx` ends up **strictly under 200 lines** (file size convention target):
   - A `useGenerationModels` hook for the enabled-models fetch + state selection.
   - A `useParentSpecTree(rootNeedId)` hook owning `specs` + `loadSpecTree` + the refresh callback.
   - A `useParentBlacklist(parent)` hook owning `blacklistCount` + load + refresh-after-add.
   - A `useClassifyingSpecs()` hook owning the `classifyingSpecIds` Set + add/remove helpers.
   Pick the minimal cut that gets under 200; don't over-extract. Each new file ≤ 200 lines. Refactor is behavior-preserving: every existing test must continue to pass without modification (other than the new tests for F1/F2).

4. **Tests** (deterministic):
   - F1 regression: mock `fetchNeedSpecTree` to reject after a successful `createNeedSpec`. Assert the Spec disappears from `classifyingSpecIds` (rendered: no "Classifying…" indicator on that Spec); classify is still called once.
   - F2 regression: described above.
   - All existing slice-11/12 tests pass unchanged.

## Out of scope (build NO behavior)
Settings toggle for auto-classify (slice-11 DC1 — still deferred to settings slice), settings-driven blacklist threshold/model (slice-12 DC1 — same), parent-level blacklist counter UX (slice-12 DC2 — defer to a later tree UX slice), per-model vote persistence (slice-07 DC1 — defer), backend changes of any kind, schema changes.

## Suggested file layout (one entity/function per file, ≤200 lines)
Frontend: new hook files under `frontend/src/hooks/` (e.g., `useGenerationModels.ts`, `useParentSpecTree.ts`); slimmed-down `GenerationPanel.tsx`. New test additions in `GenerationPanel.test.tsx`; new hook unit tests where it adds value (don't redundantly test what the integration test already covers).

## Acceptance criteria
- `GenerationPanel.tsx` is **strictly under 200 lines**.
- F1 regression test passes; manually verifiable that no permanent "Classifying…" state can occur after a tree-refresh failure.
- F2 regression test passes; blacklist failure remains silent except for `console.warn`.
- Every pre-slice-13 test in the frontend passes unchanged (no test edits to make them pass — only additions allowed).
- Backend pytest passes unchanged.
- Handoff in `docs/exchange/slice-13.md` with an acceptance-to-test mapping and a one-line note of which extraction was chosen for F3.

## Constraints
- No new features. No backend changes. No new endpoints. No schema changes. Pure frontend hygiene. Keep `useEffect` semantics identical to the current behavior — fetch-once-per-parent-change, etc. Do not parametrize or "generalize" anything beyond what F1/F2/F3 require. One branch, one PR, no self-merge.
