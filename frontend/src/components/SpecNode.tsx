import { useState } from 'react'
import type { SpecDecision } from '../api/decisions'
import { updateSpecText } from '../api/specs'
import type { ClassificationVote } from '../types/classification'
import type { SpecInspection } from '../types/inspection'
import type { SpecTreeNode } from '../types/spec'
import { ManualSpecForm } from './ManualSpecForm'
import { SpecEditor } from './SpecEditor'
import { SpecInspectionDetails } from './SpecInspectionDetails'

type SpecNodeProps = {
  classifyingSpecIds: Set<number>
  complexityBySpec: Record<number, number>
  inspectionBySpec: Record<number, SpecInspection>
  loadingInspectionId: number | null
  loadingSpecId: number | null
  onClassify: (spec: SpecTreeNode) => void
  onDecide: (spec: SpecTreeNode, decision: SpecDecision) => void
  onInspect: (spec: SpecTreeNode) => void
  onSelectSpec?: (spec: SpecTreeNode) => void
  onSpecChanged?: () => void
  selectedSpecId?: number | null
  spec: SpecTreeNode
  statusBySpec: Record<number, string>
  votesBySpec: Record<number, ClassificationVote[]>
}

function voteTooltip(votes: ClassificationVote[] | undefined): string {
  if (votes === undefined || votes.length === 0) {
    return 'No classification votes yet'
  }
  return votes.map((vote) => `Model ${vote.model_id}: ${vote.vote}`).join('\n')
}

function statusClasses(status: string): string {
  if (status === 'accepted') {
    return 'bg-green-100 text-green-700'
  }
  if (status === 'rejected') {
    return 'bg-red-100 text-red-700 line-through'
  }
  return 'bg-neutral-100 text-neutral-700'
}

export function SpecNode({
  classifyingSpecIds,
  complexityBySpec,
  inspectionBySpec,
  loadingInspectionId,
  loadingSpecId,
  onClassify,
  onDecide,
  onInspect,
  onSelectSpec,
  onSpecChanged,
  selectedSpecId,
  spec,
  statusBySpec,
  votesBySpec,
}: SpecNodeProps) {
  const complexity = complexityBySpec[spec.id] ?? spec.complexity
  const inspection = inspectionBySpec[spec.id]
  const status = statusBySpec[spec.id] ?? spec.status
  const isSelected = selectedSpecId === spec.id
  const isAutoClassifying = classifyingSpecIds.has(spec.id)
  const [isAdding, setIsAdding] = useState(false)
  const [isEditing, setIsEditing] = useState(false)

  async function handleSave(text: string) {
    await updateSpecText(spec.id, text)
    setIsEditing(false)
    onSpecChanged?.()
  }

  return (
    <li
      className={`rounded-md border bg-white p-3 text-sm ${
        isSelected ? 'border-blue-500 border-l-4 bg-blue-50 font-medium' : 'border-neutral-200'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        {isEditing ? (
          <SpecEditor initialText={spec.statement} onCancel={() => setIsEditing(false)} onSave={handleSave} />
        ) : (
          <button
            className="min-w-0 flex-1 text-left text-neutral-950"
            onClick={() => onSelectSpec?.(spec)}
            type="button"
          >
            <span className="mr-2 font-semibold text-neutral-700">{spec.req_id ?? 'REQ-UNASSIGNED'}</span>
            {spec.statement}
          </button>
        )}
        <span className="rounded bg-neutral-100 px-2 py-1 text-xs text-neutral-700">
          {spec.source === 'manual' ? 'Manual' : 'AI'}
        </span>
        <span className="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700">
          {spec.layer_name}
        </span>
        <span className={`rounded px-2 py-1 text-xs ${statusClasses(status)}`}>{status}</span>
        <span
          className="rounded bg-neutral-100 px-2 py-1 text-xs text-neutral-700"
          title={voteTooltip(votesBySpec[spec.id])}
        >
          {complexity ?? '—'}
        </span>
        {isAutoClassifying && (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-blue-700">
            <span
              aria-hidden="true"
              className="inline-block h-3 w-3 animate-spin rounded-full border border-blue-200 border-t-blue-600"
            />
            Classifying...
          </span>
        )}
        <button
          className="text-xs font-medium text-neutral-900"
          disabled={loadingSpecId === spec.id}
          onClick={() => onClassify(spec)}
          type="button"
        >
          {loadingSpecId === spec.id ? 'Classifying...' : 'Classify'}
        </button>
        <button
          className="text-xs font-medium text-neutral-900 disabled:text-neutral-400"
          disabled={loadingInspectionId === spec.id}
          onClick={() => onInspect(spec)}
          type="button"
        >
          {loadingInspectionId === spec.id ? 'Inspecting...' : 'Inspect'}
        </button>
        <button className="text-xs font-medium text-neutral-900" onClick={() => setIsEditing(true)} type="button">
          Edit
        </button>
        <button className="text-xs font-medium text-neutral-900" onClick={() => setIsAdding(true)} type="button">
          Add requirement
        </button>
        <button className="text-xs text-green-700" onClick={() => onDecide(spec, 'accepted')} type="button">
          Accept
        </button>
        <button className="text-xs text-red-600" onClick={() => onDecide(spec, 'rejected')} type="button">
          Reject
        </button>
      </div>
      {isAdding && (
        <ManualSpecForm
          onCancel={() => setIsAdding(false)}
          onCreated={() => {
            setIsAdding(false)
            onSpecChanged?.()
          }}
          parent={{ kind: 'spec', id: spec.id, layer_id: spec.layer_id }}
        />
      )}
      {inspection && <SpecInspectionDetails inspection={inspection} />}
      {spec.children.length > 0 && (
        <ul className="mt-2 space-y-2 border-l border-neutral-200 pl-4">
          {spec.children.map((child) => (
            <SpecNode
              classifyingSpecIds={classifyingSpecIds}
              complexityBySpec={complexityBySpec}
              inspectionBySpec={inspectionBySpec}
              key={child.id}
              loadingInspectionId={loadingInspectionId}
              loadingSpecId={loadingSpecId}
              onClassify={onClassify}
              onDecide={onDecide}
              onInspect={onInspect}
              onSelectSpec={onSelectSpec}
              onSpecChanged={onSpecChanged}
              selectedSpecId={selectedSpecId}
              spec={child}
              statusBySpec={statusBySpec}
              votesBySpec={votesBySpec}
            />
          ))}
        </ul>
      )}
    </li>
  )
}
