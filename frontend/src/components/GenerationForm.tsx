import type { FormEvent } from 'react'
import type { Layer } from '../types/layer'
import type { Model } from '../types/model'
import { LayerSelect } from './LayerSelect'

type GenerationFormProps = {
  allowedLayers: Layer[]
  count: number
  isGenerating: boolean
  modelId: number | null
  models: Model[]
  onCountChange: (count: number) => void
  onGenerate: (event: FormEvent<HTMLFormElement>) => void
  onLayerChange: (layerId: number) => void
  onModelIdChange: (modelId: number) => void
  selectedLayerId: number | null
}

export function GenerationForm({
  allowedLayers,
  count,
  isGenerating,
  modelId,
  models,
  onCountChange,
  onGenerate,
  onLayerChange,
  onModelIdChange,
  selectedLayerId,
}: GenerationFormProps) {
  return (
    <form className="mt-3 flex flex-wrap items-end gap-3" onSubmit={onGenerate}>
      <label className="grid gap-1 text-xs font-medium text-neutral-600">
        Model
        <select
          aria-label="Generation model"
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm font-normal text-neutral-900"
          disabled={models.length === 0}
          onChange={(event) => onModelIdChange(Number(event.target.value))}
          value={modelId ?? ''}
        >
          {models.length === 0 && <option value="">No enabled models</option>}
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
      </label>
      <LayerSelect
        layers={allowedLayers}
        onLayerChange={onLayerChange}
        selectedLayerId={selectedLayerId}
      />
      <label className="grid gap-1 text-xs font-medium text-neutral-600">
        Count
        <input
          aria-label="Generation count"
          className="w-24 rounded-md border border-neutral-300 px-3 py-2 text-sm font-normal text-neutral-900"
          max={10}
          min={1}
          onChange={(event) => onCountChange(Number(event.target.value))}
          type="number"
          value={count}
        />
      </label>
      <button
        className="rounded-md bg-neutral-950 px-3 py-2 text-sm text-white disabled:bg-neutral-400"
        disabled={isGenerating || modelId === null || selectedLayerId === null}
        type="submit"
      >
        {isGenerating ? 'Generating...' : 'Generate'}
      </button>
    </form>
  )
}
