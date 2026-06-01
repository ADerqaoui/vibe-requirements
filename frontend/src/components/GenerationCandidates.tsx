import type { GenerationCandidate } from '../types/generation'

type GenerationCandidatesProps = {
  candidates: GenerationCandidate[]
  onAccept: (candidate: GenerationCandidate) => void
  onReject: (candidate: GenerationCandidate) => void
}

export function GenerationCandidates({
  candidates,
  onAccept,
  onReject,
}: GenerationCandidatesProps) {
  return (
    <ul className="mt-4 space-y-2">
      {candidates.map((candidate) => (
        <li className="rounded-md border border-neutral-200 bg-white p-3" key={candidate.index}>
          <p className="text-sm text-neutral-950">{candidate.statement}</p>
          <div className="mt-2 flex gap-3">
            <button
              className="text-xs font-medium text-neutral-900"
              onClick={() => onAccept(candidate)}
              type="button"
            >
              Accept
            </button>
            <button
              className="text-xs text-red-600"
              onClick={() => onReject(candidate)}
              type="button"
            >
              Reject
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}
