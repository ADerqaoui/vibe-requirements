import { useEffect, useState } from 'react'
import { fetchPromptVersions, promotePromptVersion } from '../api/prompts'
import type { PromptVersion } from '../types/prompt'

type PromptHistoryProps = {
  task: string
  onClose: () => void
  onPromoted: () => void
}

function toMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function PromptHistory({ task, onClose, onPromoted }: PromptHistoryProps) {
  const [versions, setVersions] = useState<PromptVersion[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  async function loadVersions() {
    setIsLoading(true)
    try {
      setVersions(await fetchPromptVersions(task))
      setError(null)
    } catch (loadError: unknown) {
      setError(toMessage(loadError))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadVersions()
  }, [task])

  async function handlePromote(promptId: number) {
    try {
      await promotePromptVersion(promptId)
      await loadVersions()
      onPromoted()
    } catch (promoteError: unknown) {
      setError(toMessage(promoteError))
    }
  }

  return (
    <div className="mt-3 rounded-md border border-neutral-200 p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium text-neutral-900">History</p>
        <button className="rounded border border-neutral-300 px-2 py-1 text-xs" onClick={onClose} type="button">
          Close
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {isLoading ? <p className="mt-2 text-sm text-neutral-500">Loading history...</p> : null}
      <ul className="mt-2 space-y-2">
        {versions.map((version) => (
          <li className="rounded border border-neutral-200 p-2" key={version.id}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm text-neutral-800">
                v{version.version}{' '}
                {version.enabled ? <span className="text-xs font-medium text-green-700">Active</span> : null}
              </p>
              {!version.enabled ? (
                <button
                  className="rounded bg-neutral-900 px-2 py-1 text-xs text-white"
                  onClick={() => void handlePromote(version.id)}
                  type="button"
                >
                  Promote
                </button>
              ) : null}
            </div>
            <p className="mt-1 text-xs text-neutral-500">Created {version.created_at}</p>
            <details className="mt-1">
              <summary className="cursor-pointer text-xs font-medium text-neutral-700">Template</summary>
              <pre className="mt-2 max-h-40 overflow-auto rounded bg-neutral-50 p-2 text-xs text-neutral-800">
                {version.template}
              </pre>
            </details>
          </li>
        ))}
      </ul>
    </div>
  )
}
