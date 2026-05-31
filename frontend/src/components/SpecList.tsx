import { useState } from 'react'
import { classifySpec } from '../api/classification'
import type { ClassificationVote } from '../types/classification'
import type { Spec } from '../types/spec'

type SpecListProps = {
  specs: Spec[]
}

function voteTooltip(votes: ClassificationVote[] | undefined): string {
  if (votes === undefined || votes.length === 0) {
    return 'No classification votes yet'
  }
  return votes.map((vote) => `Model ${vote.model_id}: ${vote.vote}`).join('\n')
}

export function SpecList({ specs }: SpecListProps) {
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
        {specs.map((spec) => {
          const complexity = complexityBySpec[spec.id] ?? spec.complexity
          return (
            <li className="rounded-md border border-neutral-200 bg-white p-3 text-sm" key={spec.id}>
              <div className="flex items-start justify-between gap-3">
                <p className="min-w-0 flex-1 text-neutral-950">{spec.statement}</p>
                <span
                  className="rounded bg-neutral-100 px-2 py-1 text-xs text-neutral-700"
                  title={voteTooltip(votesBySpec[spec.id])}
                >
                  {complexity ?? '—'}
                </span>
                <button
                  className="text-xs font-medium text-neutral-900"
                  disabled={loadingSpecId === spec.id}
                  onClick={() => handleClassify(spec)}
                  type="button"
                >
                  {loadingSpecId === spec.id ? 'Classifying...' : 'Classify'}
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </>
  )
}
