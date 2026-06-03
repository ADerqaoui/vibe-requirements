import { FormEvent, useState } from 'react'
import { createPromptVersion, PromptTemplateInvalidApiError } from '../api/prompts'
import type { Prompt } from '../types/prompt'

type PromptEditorProps = {
  prompt: Prompt
  onCancel: () => void
  onSaved: () => void
}

function messageFor(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function PromptEditor({ prompt, onCancel, onSaved }: PromptEditorProps) {
  const [template, setTemplate] = useState(prompt.template)
  const [name, setName] = useState(prompt.name)
  const [description, setDescription] = useState(prompt.description ?? '')
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setError(null)
    try {
      await createPromptVersion(prompt.task, {
        template,
        name: name.trim() || undefined,
        description: description.trim() || undefined,
      })
      onSaved()
    } catch (saveError: unknown) {
      if (saveError instanceof PromptTemplateInvalidApiError) {
        setError(saveError.reason)
      } else {
        setError(messageFor(saveError))
      }
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form className="mt-3 space-y-2 rounded-md border border-neutral-200 p-3" onSubmit={handleSubmit}>
      <label className="block text-xs font-medium text-neutral-700">
        Name
        <input
          className="mt-1 w-full rounded border border-neutral-300 px-2 py-1 text-sm"
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
      </label>
      <label className="block text-xs font-medium text-neutral-700">
        Description
        <input
          className="mt-1 w-full rounded border border-neutral-300 px-2 py-1 text-sm"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </label>
      <label className="block text-xs font-medium text-neutral-700">
        Template
        <textarea
          className="mt-1 h-48 w-full rounded border border-neutral-300 px-2 py-1 font-mono text-xs"
          value={template}
          onChange={(event) => setTemplate(event.target.value)}
        />
      </label>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button className="rounded bg-neutral-900 px-3 py-1 text-sm text-white" disabled={isSaving} type="submit">
          {isSaving ? 'Saving...' : 'Save'}
        </button>
        <button className="rounded border border-neutral-300 px-3 py-1 text-sm" onClick={onCancel} type="button">
          Cancel
        </button>
      </div>
    </form>
  )
}
