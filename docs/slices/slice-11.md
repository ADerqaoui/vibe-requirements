# Slice 11 — Auto-classify on Accept (frontend chain)

Branch: `slice-11` (from `main`). Scope: when a candidate is **Accepted** (Need→Spec from slice-06, or Spec→child-Spec from slice-09), the new Spec is **automatically classified** via the slice-07 classification service immediately. Removes the "click Classify on every new Spec" friction. **Frontend-only chain** — no backend changes, no new endpoints, no schema. Best-effort: if classification fails, the Spec persists without a complexity badge; the User can manually Classify it later.

## In scope
1. **Frontend chain on Accept** — in the component that owns the Accept handler (`GenerationPanel.tsx` or wherever the Accept button lives after the slice-10 split): (1) POST to the existing create-spec endpoint (`/api/needs/{id}/specs` or `/api/specs/{id}/specs` per parent), (2) on success, immediately POST `/api/specs/{newSpecId}/classify`. On classify failure, log to `console.warn` and continue — the Spec exists, just unclassified; no error UI blocks the user.
2. **"Classifying…" indicator** — while a classify call is in flight on a newly-Accepted Spec, render a small inline "Classifying…" state (text + small spinner) on that Spec's card in the tree. On resolve (success or failure), remove the indicator. The set of currently-classifying spec ids lives in the tree-owning component (the one that already owns `selectedParent` and the spec-tree refresh) and is passed down to the recursive SpecList.
3. **Refresh badge after classify resolves** — either update the affected Spec's `complexity` in-place from the classify response, or trigger the existing `/api/needs/{id}/spec-tree` refetch a second time after classify resolves. Pick the cheaper option; document the choice in the handoff.
4. **Manual Classify still works unchanged** — the existing Classify button continues to operate per slice 07; it just won't usually be needed.
5. **Tests** (deterministic, no live network):
   - Accept chain (success): mocked create returns a new Spec; classify is called with the new Spec's id; the "Classifying…" indicator is on that Spec during the in-flight period; on resolve the indicator disappears and the complexity badge appears.
   - Accept chain (classify failure): Spec persists; indicator disappears; no complexity badge; no error UI; manual Classify still works on that Spec.
   - Order assertion: create-spec is called BEFORE classify, and classify uses the id from the create response.
   - Regression: manual Classify path remains unchanged (existing slice-07 test still passes).

## Out of scope (build NO behavior)
Backend changes (no new endpoints, no atomic create-and-classify), settings toggle for auto-classify (always-on this slice; toggle is a later settings-panel concern), auto-inspect on Accept (separate slice), re-classify on Spec edit, classification result caching, Router ON / auto model+prompt selection, cloud adapters, blacklist.

## Suggested file layout (one entity/function per file, ≤200 lines)
Frontend: extend the Accept handler in `src/components/GenerationPanel.tsx` (or the post-split owner) to chain classify; thread a `classifyingSpecIds: Set<number>` (or equivalent) through `SpecList.tsx`/`SpecNode.tsx` for the indicator; reuse `src/api/classification.ts` from slice 07 unchanged. Tests: extend `GenerationPanel.test.tsx` for the chain + indicator + failure-path scenarios; small additions to `SpecNode.test.tsx` for the indicator rendering.

## Acceptance criteria
- After Accept on a candidate (Need-parent or Spec-parent), the new Spec appears in the tree with a brief "Classifying…" indicator.
- The classification API is called exactly once with the new Spec's id.
- When classify resolves successfully, the complexity badge appears on the new Spec; the indicator disappears.
- If classify fails, the Spec persists without a complexity badge; no error blocks the user; the existing manual Classify button still works on that Spec.
- Manual Classify (slice 07) path is unchanged.
- `pytest` + `pnpm test` pass. Handoff in `docs/exchange/slice-11.md` with an acceptance-to-test mapping.

## Constraints
- No backend changes, no new endpoints, no schema. Single chained classify call per Accept; do not parallelize across multiple Accepts in one slice. Reuse the existing classify API (`POST /api/specs/{id}/classify`) and complexity-badge rendering — do not introduce a competing classification UI pattern. One branch, one PR, no self-merge.
