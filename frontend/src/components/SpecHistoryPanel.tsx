import { useEffect, useState } from 'react'
import { fetchSpecRevisions } from '../api/specs'
import type { SpecRevision } from '../types/spec'

type SpecHistoryPanelProps = {
  specId: number
  onClose: () => void
}

const CHANGE_LABELS: Record<string, string> = {
  created: 'Created',
  text_edited: 'Text edited',
  status_changed: 'Status changed',
}

function changeLabel(changeType: string): string {
  return CHANGE_LABELS[changeType] ?? changeType
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function SpecHistoryPanel({ specId, onClose }: SpecHistoryPanelProps) {
  const [revisions, setRevisions] = useState<SpecRevision[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let didCancel = false
    fetchSpecRevisions(specId)
      .then((loadedRevisions) => {
        if (didCancel) {
          return
        }
        setRevisions(loadedRevisions)
        setError(null)
      })
      .catch((loadError: unknown) => {
        if (!didCancel) {
          setError(errorMessage(loadError))
        }
      })
      .finally(() => {
        if (!didCancel) {
          setIsLoading(false)
        }
      })
    return () => {
      didCancel = true
    }
  }, [specId])

  return (
    <section className="mt-3 rounded-md border border-neutral-200 bg-neutral-50 p-3">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-semibold text-neutral-900">History</h4>
        <button className="text-xs font-medium text-neutral-700" onClick={onClose} type="button">
          Close
        </button>
      </div>
      {isLoading && <p className="mt-2 text-sm text-neutral-500">Loading history...</p>}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <ol className="mt-3 space-y-3">
        {revisions.map((revision) => (
          <li key={revision.revision_number} className="rounded border border-neutral-200 bg-white p-3">
            <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-600">
              <span className="font-semibold text-neutral-900">
                {revision.revision_number}. {changeLabel(revision.change_type)}
              </span>
              <span>{revision.created_at}</span>
              <span className="rounded bg-neutral-100 px-2 py-1">{revision.status}</span>
              <span className="rounded bg-neutral-100 px-2 py-1">
                {revision.source === 'manual' ? 'Manual' : 'AI'}
              </span>
            </div>
            <p className="mt-2 whitespace-pre-wrap text-sm text-neutral-900">{revision.text}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}
