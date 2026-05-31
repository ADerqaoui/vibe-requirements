import type { FormEvent } from 'react'

export type NeedDraft = {
  statement: string
  context: string
  constraints: string
}

type NeedCreateFormProps = {
  draft: NeedDraft
  onDraftChange: (draft: NeedDraft) => void
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
}

export function NeedCreateForm({ draft, onDraftChange, onSubmit }: NeedCreateFormProps) {
  return (
    <form className="mt-4 grid gap-2" onSubmit={onSubmit}>
      <input
        aria-label="Need statement"
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
        onChange={(event) => onDraftChange({ ...draft, statement: event.target.value })}
        placeholder="Statement"
        value={draft.statement}
      />
      <input
        aria-label="Need context"
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
        onChange={(event) => onDraftChange({ ...draft, context: event.target.value })}
        placeholder="Context"
        value={draft.context}
      />
      <input
        aria-label="Need constraints"
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
        onChange={(event) => onDraftChange({ ...draft, constraints: event.target.value })}
        placeholder="Constraints"
        value={draft.constraints}
      />
      <button className="w-fit rounded-md bg-neutral-950 px-3 py-2 text-sm text-white" type="submit">
        Add need
      </button>
    </form>
  )
}
