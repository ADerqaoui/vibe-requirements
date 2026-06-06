# Slice 27 — Fix cramped spec-text layout in SpecNode

Branch: `slice-27` (from `main`). Scope: fix the spec-tree row layout so the requirement text spans the full panel width instead of collapsing into a narrow column. **Frontend-only, layout-only — no behavior, API, or data changes.** This is a reported bug: in `SpecNode.tsx` the requirement text, four badges, and seven action buttons all share one `flex flex-wrap justify-between` row, which squeezes the `flex-1` text into a thin column.

## In scope

1. **Restructure the `SpecNode` row** from one horizontal flex row into a vertical stack of two rows:
   - **Row 1 — the requirement (full width):** the `req_id` + `statement` button (or the `SpecEditor` when editing) on its own line, taking the full available width (`w-full`, left-aligned). Keep the existing select behavior (`onSelectSpec`), the selected styling, and the `REQ-UNASSIGNED` fallback.
   - **Row 2 — metadata + actions (wraps):** the source badge (AI/Manual), layer badge, status badge, complexity badge, the "Classifying…" indicator, and all action buttons (Classify, Inspect, Edit, History, Add requirement, Accept, Reject) in a `flex flex-wrap items-center gap-2` row below the text.
   - The nested children list, `ManualSpecForm`, `SpecHistoryPanel`, and `SpecInspectionDetails` render below as today.

2. **No behavior changes.** Every button keeps its exact handler, disabled state, and label logic (`onClassify`, `onInspect`, `onDecide`, edit/history/add toggles, loading states). Only the DOM/container structure and Tailwind classes change. The edit state (`SpecEditor`) now occupies the full-width row-1 slot instead of being wedged beside the badges.

3. **Consistency check:** if the same cramped pattern exists in the generation candidate list rendering (the candidates produced by Generate), apply the same two-row treatment there; otherwise leave it. State in the handoff whether candidates needed it.

4. **Constraints:** keep `SpecNode.tsx` (and any touched file) strictly under 200 lines. Do not change props, types, API calls, or any parent component's data flow. Do not restyle colors/spacing beyond what's needed to achieve the two-row layout.

## Out of scope (build NO behavior)
- Any backend, API, schema, or data change.
- Changing what the action buttons do, adding/removing actions, or collapsing them into a menu.
- The blacklist bug or the (already-fixed) accept bug — separate.
- Redesigning badges, colors, typography, or the overall panel beyond the row restructure.
- Responsive breakpoints beyond the natural `flex-wrap` behavior.

## Tests
- Existing `SpecNode.test.tsx` assertions continue to pass unchanged (all buttons present and wired; decide/classify/inspect/edit/history/add still invoke their handlers; status/complexity/source/layer still render).
- Add a light assertion that the requirement text and the action row are distinct rows (e.g. the statement is not in the same flex container as the Accept button) — enough to lock the two-row structure so a future edit doesn't silently re-cram them. Don't over-test layout.
- `pnpm test` + `pnpm typecheck` + `pnpm build` all green.

## Acceptance criteria
- In the spec tree, the requirement text uses the full width of the panel and wraps naturally over the available space (no thin column); badges and action buttons sit on a row beneath it.
- All spec-node actions behave exactly as before.
- `SpecNode.tsx` stays under 200 lines; `pnpm test` + `pnpm typecheck` + `pnpm build` green. Handoff in `docs/exchange/slice-27.md` with the candidate-list note and an acceptance-to-test mapping.

## Constraints
- Frontend-only, layout-only. No props/types/API/data changes. Preserve every handler and state behavior. One branch, one PR, no self-merge. All frontend checks green per docs/MERGE-CHECKLIST.md (backend untouched, but run pytest once to confirm no incidental breakage).