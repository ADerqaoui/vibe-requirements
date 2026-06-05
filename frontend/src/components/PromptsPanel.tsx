import { useEffect, useState } from 'react'
import { fetchLayers } from '../api/layers'
import { fetchPrompts, fetchPromptVariants } from '../api/prompts'
import type { Layer } from '../types/layer'
import type { Prompt } from '../types/prompt'
import { PromptTaskGroup, type PromptVariantEntry } from './PromptTaskGroup'

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

function groupByTask(prompts: PromptVariantEntry[]): Map<string, PromptVariantEntry[]> {
  const groups = new Map<string, PromptVariantEntry[]>()
  prompts.forEach((prompt) => {
    groups.set(prompt.task, [...(groups.get(prompt.task) ?? []), prompt])
  })
  return groups
}

export function PromptsPanel() {
  const [prompts, setPrompts] = useState<PromptVariantEntry[]>([])
  const [layers, setLayers] = useState<Layer[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [historyKey, setHistoryKey] = useState<string | null>(null)

  async function loadPrompts(shouldCancel: () => boolean = () => false) {
    try {
      const [loadedPrompts, loadedLayers] = await Promise.all([fetchPromptEntries(), fetchLayers()])
      if (shouldCancel()) {
        return
      }
      setPrompts(loadedPrompts)
      setLayers(loadedLayers)
      setError(null)
    } catch (loadError: unknown) {
      if (!shouldCancel()) {
        setError(toErrorMessage(loadError))
      }
    } finally {
      if (!shouldCancel()) {
        setIsLoading(false)
      }
    }
  }

  useEffect(() => {
    let didCancel = false
    void loadPrompts(() => didCancel)
    return () => {
      didCancel = true
    }
  }, [])

  async function refreshAfterChange() {
    setIsLoading(true)
    await loadPrompts()
    setEditingKey(null)
    setHistoryKey(null)
  }

  const groups = groupByTask(prompts)

  return (
    <section className="mt-5 rounded-md border border-neutral-200 bg-white p-3">
      <h3 className="text-sm font-semibold text-neutral-900">Prompts</h3>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {isLoading ? <p className="mt-2 text-sm text-neutral-500">Loading prompts...</p> : null}
      <ul className="mt-3 space-y-2">
        {[...groups.entries()].map(([task, taskPrompts]) => (
          <PromptTaskGroup
            key={task}
            task={task}
            prompts={taskPrompts}
            layers={layers}
            editingKey={editingKey}
            historyKey={historyKey}
            onEdit={setEditingKey}
            onHistory={setHistoryKey}
            onCancelEdit={() => setEditingKey(null)}
            onCloseHistory={() => setHistoryKey(null)}
            onChanged={() => void refreshAfterChange()}
          />
        ))}
      </ul>
    </section>
  )
}

async function fetchPromptEntries(): Promise<PromptVariantEntry[]> {
  const defaults = await fetchPrompts()
  const nestedEntries = await Promise.all(defaults.map(expandPromptVariants))
  return nestedEntries.flat()
}

async function expandPromptVariants(prompt: Prompt): Promise<PromptVariantEntry[]> {
  const variants = await fetchPromptVariants(prompt.task, prompt.layer_id)
  return variants.map((variant) => ({
    ...prompt,
    name: variant.name,
    version: variant.version,
    template: variant.template,
    prompt_id: variant.prompt_id,
    is_default: variant.is_default,
  }))
}
