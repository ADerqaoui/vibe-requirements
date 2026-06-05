import type { SpecDecision } from '../api/decisions'
import type { ClassificationVote } from '../types/classification'
import type { SpecInspection } from '../types/inspection'
import type { SpecTreeNode } from '../types/spec'

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

function verdictClasses(verdict: string): string {
  if (verdict === 'PASS') {
    return 'bg-green-100 text-green-700'
  }
  if (verdict === 'FAIL') {
    return 'bg-red-100 text-red-700'
  }
  return 'bg-amber-100 text-amber-700'
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

  return (
    <li
      className={`rounded-md border bg-white p-3 text-sm ${
        isSelected ? 'border-blue-500 border-l-4 bg-blue-50 font-medium' : 'border-neutral-200'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <button
          className="min-w-0 flex-1 text-left text-neutral-950"
          onClick={() => onSelectSpec?.(spec)}
          type="button"
        >
          {spec.statement}
        </button>
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
        <button className="text-xs text-green-700" onClick={() => onDecide(spec, 'accepted')} type="button">
          Accept
        </button>
        <button className="text-xs text-red-600" onClick={() => onDecide(spec, 'rejected')} type="button">
          Reject
        </button>
      </div>
      {inspection && (
        <div className="mt-3 rounded-md border border-neutral-200 bg-neutral-50 p-3">
          {inspection.selected_model_name && (
            <p className="mb-2 text-xs text-neutral-600">Inspected with: {inspection.selected_model_name}</p>
          )}
          {inspection.selected_prompt_name && (
            <p className="mb-2 text-xs text-neutral-600">Prompt: {inspection.selected_prompt_name}</p>
          )}
          <ul className="space-y-1">
            {inspection.findings.criteria.map((criterion) => (
              <li className="flex flex-wrap gap-2 text-xs" key={criterion.name}>
                <span className={`rounded px-2 py-0.5 font-medium ${verdictClasses(criterion.verdict)}`}>
                  {criterion.verdict}
                </span>
                <span className="font-medium text-neutral-800">{criterion.name}</span>
                <span className="text-neutral-600">{criterion.note}</span>
              </li>
            ))}
          </ul>
          {inspection.findings.summary && (
            <p className="mt-2 text-xs text-neutral-600">{inspection.findings.summary}</p>
          )}
        </div>
      )}
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
