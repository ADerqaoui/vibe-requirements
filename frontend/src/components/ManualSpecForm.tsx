import { useCallback, useState } from 'react'
import { createManualChildSpec, createManualNeedSpec } from '../api/specs'
import { useAllowedChildLayers } from '../hooks/useAllowedChildLayers'
import type { GenerationParent } from '../types/generationParent'
import { errorMessage } from '../utils/errorMessage'

type ManualSpecFormProps = {
  onCancel: () => void
  onCreated: () => void
  parent: GenerationParent
}

export function ManualSpecForm({ onCancel, onCreated, parent }: ManualSpecFormProps) {
  const [text, setText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const handleLayerError = useCallback((loadError: unknown) => setError(errorMessage(loadError)), [])
  const { allowedLayers, selectedLayerId, setSelectedLayerId } = useAllowedChildLayers(parent, handleLayerError)
  const trimmedText = text.trim()

  async function handleSave() {
    if (trimmedText === '' || selectedLayerId === null) {
      return
    }
    setIsSaving(true)
    try {
      const payload = { text: trimmedText, target_layer_id: selectedLayerId }
      if (parent.kind === 'need') {
        await createManualNeedSpec(parent.id, payload)
      } else {
        await createManualChildSpec(parent.id, payload)
      }
      setError(null)
      onCreated()
    } catch (saveError: unknown) {
      setError(errorMessage(saveError))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="mt-3 grid gap-2 rounded-md border border-neutral-200 bg-neutral-50 p-3">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <label className="grid gap-1 text-xs font-medium text-neutral-600">
        Layer
        <select
          aria-label="Manual requirement layer"
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm font-normal text-neutral-900"
          disabled={allowedLayers.length === 0}
          onChange={(event) => setSelectedLayerId(Number(event.target.value))}
          value={selectedLayerId ?? ''}
        >
          {allowedLayers.map((layer) => (
            <option key={layer.id} value={layer.id}>
              {layer.name}
            </option>
          ))}
        </select>
      </label>
      <textarea
        aria-label="Manual requirement text"
        className="min-h-24 rounded-md border border-neutral-300 px-3 py-2 text-sm text-neutral-900"
        onChange={(event) => setText(event.target.value)}
        value={text}
      />
      <div className="flex gap-2">
        <button
          className="rounded bg-neutral-900 px-3 py-1.5 text-xs font-medium text-white disabled:bg-neutral-300"
          disabled={isSaving || trimmedText === '' || selectedLayerId === null}
          onClick={handleSave}
          type="button"
        >
          {isSaving ? 'Saving...' : 'Save'}
        </button>
        <button className="px-3 py-1.5 text-xs font-medium text-neutral-700" onClick={onCancel} type="button">
          Cancel
        </button>
      </div>
    </div>
  )
}
