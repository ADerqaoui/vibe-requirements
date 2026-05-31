import type { Need } from '../types/need'
import type { NeedDraft } from './NeedCreateForm'

type NeedRowProps = {
  editDraft: NeedDraft
  isEditing: boolean
  isSelected: boolean
  need: Need
  onBeginEdit: (need: Need) => void
  onDelete: (need: Need) => void
  onEditDraftChange: (draft: NeedDraft) => void
  onSave: (needId: number) => void
  onSelect: (needId: number) => void
}

export function NeedRow({
  editDraft,
  isEditing,
  isSelected,
  need,
  onBeginEdit,
  onDelete,
  onEditDraftChange,
  onSave,
  onSelect,
}: NeedRowProps) {
  return (
    <li
      className={`rounded-md border bg-white p-3 ${
        isSelected ? 'border-blue-500 border-l-4 bg-blue-50 font-medium' : 'border-neutral-200'
      }`}
    >
      {isEditing ? (
        <div className="grid gap-2">
          <input
            aria-label={`Edit statement ${need.id}`}
            className="rounded-md border border-neutral-300 px-2 py-1 text-sm"
            onChange={(event) => onEditDraftChange({ ...editDraft, statement: event.target.value })}
            value={editDraft.statement}
          />
          <input
            aria-label={`Edit context ${need.id}`}
            className="rounded-md border border-neutral-300 px-2 py-1 text-sm"
            onChange={(event) => onEditDraftChange({ ...editDraft, context: event.target.value })}
            value={editDraft.context}
          />
          <input
            aria-label={`Edit constraints ${need.id}`}
            className="rounded-md border border-neutral-300 px-2 py-1 text-sm"
            onChange={(event) => onEditDraftChange({ ...editDraft, constraints: event.target.value })}
            value={editDraft.constraints}
          />
          <button
            className="w-fit text-sm font-medium text-neutral-900"
            onClick={() => onSave(need.id)}
            type="button"
          >
            Save
          </button>
        </div>
      ) : (
        <div className="flex items-start justify-between gap-3">
          <button className="min-w-0 flex-1 text-left" onClick={() => onSelect(need.id)} type="button">
            <span className="block text-sm font-medium text-neutral-950">{need.statement}</span>
            {need.context && <span className="block text-xs text-neutral-500">{need.context}</span>}
            {need.constraints && <span className="block text-xs text-neutral-500">{need.constraints}</span>}
            {need.complexity === null && (
              <span className="mt-2 inline-block rounded bg-amber-100 px-2 py-1 text-xs text-amber-800">
                Unclassified
              </span>
            )}
          </button>
          <button className="text-xs text-neutral-500" onClick={() => onBeginEdit(need)} type="button">
            Edit
          </button>
          <button className="text-xs text-red-600" onClick={() => onDelete(need)} type="button">
            Delete
          </button>
        </div>
      )}
    </li>
  )
}
