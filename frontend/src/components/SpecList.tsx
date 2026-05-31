import { useEffect, useState } from 'react'
import { classifySpec } from '../api/classification'
import { fetchChildSpecs } from '../api/specs'
import type { ClassificationVote } from '../types/classification'
import type { Spec } from '../types/spec'

type SpecListProps = {
  specs: Spec[]
  onSelectSpec?: (spec: Spec) => void
  selectedSpecId?: number | null
}

type SpecNodeProps = {
  spec: Spec
  complexityBySpec: Record<number, number>
  votesBySpec: Record<number, ClassificationVote[]>
  loadingSpecId: number | null
  selectedSpecId?: number | null
  onClassify: (spec: Spec) => void
  onSelectSpec?: (spec: Spec) => void
}

function voteTooltip(votes: ClassificationVote[] | undefined): string {
  if (votes === undefined || votes.length === 0) {
    return 'No classification votes yet'
  }
  return votes.map((vote) => `Model ${vote.model_id}: ${vote.vote}`).join('\n')
}

export function SpecList({ specs, onSelectSpec, selectedSpecId }: SpecListProps) {
  const [complexityBySpec, setComplexityBySpec] = useState<Record<number, number>>({})
  const [votesBySpec, setVotesBySpec] = useState<Record<number, ClassificationVote[]>>({})
  const [loadingSpecId, setLoadingSpecId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleClassify(spec: Spec) {
    setLoadingSpecId(spec.id)
    try {
      const result = await classifySpec(spec.id)
      setComplexityBySpec((currentValues) => ({
        ...currentValues,
        [spec.id]: result.complexity,
      }))
      setVotesBySpec((currentValues) => ({ ...currentValues, [spec.id]: result.votes }))
      setError(null)
    } catch (classifyError: unknown) {
      setError(classifyError instanceof Error ? classifyError.message : String(classifyError))
    } finally {
      setLoadingSpecId(null)
    }
  }

  if (specs.length === 0) {
    return <p className="mt-2 text-sm text-neutral-500">No specs accepted yet.</p>
  }

  return (
    <>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <ul className="mt-2 space-y-2">
        {specs.map((spec) => (
          <SpecNode
            complexityBySpec={complexityBySpec}
            key={spec.id}
            loadingSpecId={loadingSpecId}
            onClassify={handleClassify}
            onSelectSpec={onSelectSpec}
            selectedSpecId={selectedSpecId}
            spec={spec}
            votesBySpec={votesBySpec}
          />
        ))}
      </ul>
    </>
  )
}

function SpecNode({
  spec,
  complexityBySpec,
  votesBySpec,
  loadingSpecId,
  selectedSpecId,
  onClassify,
  onSelectSpec,
}: SpecNodeProps) {
  const [children, setChildren] = useState<Spec[]>([])
  const [error, setError] = useState<string | null>(null)
  const complexity = complexityBySpec[spec.id] ?? spec.complexity
  const isSelected = selectedSpecId === spec.id

  useEffect(() => {
    let didCancel = false
    fetchChildSpecs(spec.id)
      .then((loadedChildren) => {
        if (didCancel) {
          return
        }
        setChildren(loadedChildren)
        setError(null)
      })
      .catch((loadError: unknown) => {
        if (!didCancel) {
          setError(loadError instanceof Error ? loadError.message : String(loadError))
        }
      })
    return () => {
      didCancel = true
    }
  }, [spec.id])

  return (
    <li
      className={`rounded-md border bg-white p-3 text-sm ${
        isSelected ? 'border-neutral-950' : 'border-neutral-200'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <button
          className="min-w-0 flex-1 text-left text-neutral-950"
          onClick={() => onSelectSpec?.(spec)}
          type="button"
        >
          {spec.statement}
        </button>
        <span
          className="rounded bg-neutral-100 px-2 py-1 text-xs text-neutral-700"
          title={voteTooltip(votesBySpec[spec.id])}
        >
          {complexity ?? '—'}
        </span>
        <button
          className="text-xs font-medium text-neutral-900"
          disabled={loadingSpecId === spec.id}
          onClick={() => onClassify(spec)}
          type="button"
        >
          {loadingSpecId === spec.id ? 'Classifying...' : 'Classify'}
        </button>
      </div>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
      {children.length > 0 && (
        <ul className="mt-2 space-y-2 border-l border-neutral-200 pl-4">
          {children.map((child) => (
            <SpecNode
              complexityBySpec={complexityBySpec}
              key={child.id}
              loadingSpecId={loadingSpecId}
              onClassify={onClassify}
              onSelectSpec={onSelectSpec}
              selectedSpecId={selectedSpecId}
              spec={child}
              votesBySpec={votesBySpec}
            />
          ))}
        </ul>
      )}
    </li>
  )
}
