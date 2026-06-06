import { FormEvent, useState } from 'react'
import { createPromptVersion, PromptTemplateInvalidApiError } from '../api/prompts'
import type { Layer } from '../types/layer'
import type { Prompt } from '../types/prompt'
import { LayerVariantPicker } from './LayerVariantPicker'
import { PromptPreviewPanel } from './PromptPreviewPanel'

type PromptEditorProps = {
  prompt: Prompt
  mode?: 'edit' | 'add-layer' | 'add-variant'
  layerOptions?: Layer[]
  onCancel: () => void
  onSaved: () => void
}

function messageFor(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

function scopeLabel(prompt: Prompt): string {
  return prompt.layer_id === null ? 'Global' : prompt.layer_name ?? `Layer ${prompt.layer_id}`
}

export function PromptEditor({
  prompt,
  mode = 'edit',
  layerOptions = [],
  onCancel,
  onSaved,
}: PromptEditorProps) {
  const [template, setTemplate] = useState(prompt.template)
  const [name, setName] = useState(mode === 'add-variant' ? '' : prompt.name)
  const [description, setDescription] = useState(prompt.description ?? '')
  const [selectedLayerId, setSelectedLayerId] = useState<number | ''>(layerOptions[0]?.id ?? '')
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (mode === 'add-layer' && selectedLayerId === '') {
      setError('Choose a layer')
      return
    }
    if (mode === 'add-variant' && name.trim() === '') {
      setError('Name the variant')
      return
    }
    setIsSaving(true)
    setError(null)
    const targetLayerId = mode === 'add-layer' ? selectedLayerId : prompt.layer_id
    if (targetLayerId === '') {
      setError('Choose a layer')
      setIsSaving(false)
      return
    }
    try {
      await createPromptVersion(prompt.task, {
        template,
        layer_id: targetLayerId,
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
      {mode === 'add-layer' ? (
        <LayerVariantPicker layers={layerOptions} value={selectedLayerId} onChange={setSelectedLayerId} />
      ) : (
        <p className="text-xs text-neutral-600">Scope: {scopeLabel(prompt)}</p>
      )}
      <label className="block text-xs font-medium text-neutral-700">
        Template
        <textarea
          className="mt-1 h-48 w-full rounded border border-neutral-300 px-2 py-1 font-mono text-xs"
          value={template}
          onChange={(event) => setTemplate(event.target.value)}
        />
      </label>
      <PromptPreviewPanel task={prompt.task} template={template} />
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
