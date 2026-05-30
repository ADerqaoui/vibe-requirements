# Merge Checklist (definition of done)

Run before merging any slice PR to `main`. All must be true.

- [ ] Branched from a merged `main` — no stacked or unmerged base.
- [ ] PR diff is a single slice only (no stray files from other slices).
- [ ] Both reviews are recorded in `docs/exchange/slice-NN.md` and read APPROVE / APPROVE-WITH-NITS — no open BLOCK.
- [ ] All User-approved findings are resolved or explicitly deferred (noted in the exchange file).
- [ ] The handoff's acceptance-to-test mapping shows every criterion covered (or a noted exception).
- [ ] `pytest` and `pnpm test` pass; the app boots.
- [ ] No scope creep beyond the slice spec.
- [ ] No `.env`, `*.db`, `*.sqlite`, `*.sql`, or secrets in the diff.
- [ ] Branch is up to date with `main` and mergeable.

After merge: delete the branch; record the merge in the slice's `## User — decisions`.
