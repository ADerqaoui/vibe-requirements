import { useEffect, useState } from 'react'
import { fetchPrompts } from '../api/prompts'
import type { Prompt } from '../types/prompt'

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

function scopeText(value: string | number | null): string {
  return value === null ? 'any' : String(value)
}

export function PromptsPanel() {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let didCancel = false
    fetchPrompts()
      .then((loadedPrompts) => {
        if (didCancel) {
          return
        }
        setPrompts(loadedPrompts)
        setError(null)
      })
      .catch((loadError: unknown) => {
        if (!didCancel) {
          setError(toErrorMessage(loadError))
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
  }, [])

  return (
    <section className="mt-5 rounded-md border border-neutral-200 bg-white p-3">
      <h3 className="text-sm font-semibold text-neutral-900">Prompts</h3>
      <p className="mt-1 text-xs text-neutral-500">Editable in a future slice.</p>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {isLoading ? <p className="mt-2 text-sm text-neutral-500">Loading prompts...</p> : null}
      <ul className="mt-3 space-y-2">
        {prompts.map((prompt) => (
          <li className="rounded-md border border-neutral-200 p-3" key={prompt.task}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-sm font-medium text-neutral-950">{prompt.name}</p>
                <p className="text-xs text-neutral-500">
                  {prompt.task} · v{prompt.version} · layer {scopeText(prompt.layer_id)} · discipline{' '}
                  {scopeText(prompt.discipline_scope)}
                </p>
              </div>
              <p className="text-xs text-neutral-500">Updated {prompt.updated_at}</p>
            </div>
            {prompt.description && <p className="mt-2 text-sm text-neutral-600">{prompt.description}</p>}
            <details className="mt-2">
              <summary className="cursor-pointer text-xs font-medium text-neutral-700">
                Template
              </summary>
              <pre className="mt-2 max-h-56 overflow-auto rounded bg-neutral-50 p-3 text-xs text-neutral-800">
                {prompt.template}
              </pre>
            </details>
          </li>
        ))}
      </ul>
    </section>
  )
}
