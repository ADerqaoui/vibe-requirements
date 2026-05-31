import { FormEvent, useMemo, useState } from 'react'
import { completeModel } from '../api/gateway'
import type { CompletionResult } from '../types/completion'
import type { Model } from '../types/model'

type ModelTesterProps = {
  models: Model[]
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function ModelTester({ models }: ModelTesterProps) {
  const enabledModels = useMemo(() => models.filter((model) => model.enabled), [models])
  const [modelId, setModelId] = useState<number | null>(enabledModels[0]?.id ?? null)
  const [prompt, setPrompt] = useState('')
  const [system, setSystem] = useState('')
  const [result, setResult] = useState<CompletionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSending, setIsSending] = useState(false)

  const selectedModelId = modelId ?? enabledModels[0]?.id ?? null

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (selectedModelId === null || prompt.trim() === '') {
      return
    }
    setIsSending(true)
    try {
      const completion = await completeModel(selectedModelId, {
        prompt,
        system: system.trim() === '' ? undefined : system,
      })
      setResult(completion)
      setError(null)
    } catch (completionError: unknown) {
      setError(errorMessage(completionError))
      setResult(null)
    } finally {
      setIsSending(false)
    }
  }

  return (
    <section className="mt-6 border-t border-neutral-200 pt-5">
      <h3 className="text-sm font-semibold text-neutral-900">Test a model</h3>
      <form className="mt-3 grid gap-3" onSubmit={handleSubmit}>
        <select
          aria-label="Test model"
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
          disabled={enabledModels.length === 0}
          onChange={(event) => setModelId(Number(event.target.value))}
          value={selectedModelId ?? ''}
        >
          {enabledModels.length === 0 && <option value="">No enabled models</option>}
          {enabledModels.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name} ({model.provider})
            </option>
          ))}
        </select>
        <textarea
          aria-label="Test system prompt"
          className="min-h-20 rounded-md border border-neutral-300 px-3 py-2 text-sm"
          onChange={(event) => setSystem(event.target.value)}
          placeholder="System prompt (optional)"
          value={system}
        />
        <textarea
          aria-label="Test prompt"
          className="min-h-28 rounded-md border border-neutral-300 px-3 py-2 text-sm"
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Prompt"
          value={prompt}
        />
        <button
          className="w-fit rounded-md bg-neutral-950 px-3 py-2 text-sm text-white disabled:bg-neutral-400"
          disabled={isSending || selectedModelId === null || prompt.trim() === ''}
          type="submit"
        >
          {isSending ? 'Sending...' : 'Send'}
        </button>
      </form>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {result && (
        <div className="mt-3 rounded-md border border-neutral-200 bg-white p-3">
          <p className="whitespace-pre-wrap text-sm text-neutral-900">{result.text}</p>
          <p className="mt-3 text-xs text-neutral-500">
            {result.in_tokens} input tokens · {result.out_tokens} output tokens ·{' '}
            {result.cost_sek.toFixed(4)} SEK · {result.duration_ms} ms
          </p>
        </div>
      )}
    </section>
  )
}
