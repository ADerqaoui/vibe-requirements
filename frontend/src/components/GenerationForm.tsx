import type { FormEvent } from 'react'
import type { Layer } from '../types/layer'
import type { Model } from '../types/model'
import { LayerSelect } from './LayerSelect'
import { ModelChoice } from './ModelChoice'

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
  routerEnabled: boolean
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
  routerEnabled,
  selectedLayerId,
}: GenerationFormProps) {
  return (
    <form className="mt-3 flex flex-wrap items-end gap-3" onSubmit={onGenerate}>
      <ModelChoice
        ariaLabel="Generation model"
        label="Model"
        modelId={modelId}
        models={models}
        onModelIdChange={onModelIdChange}
        routerEnabled={routerEnabled}
      />
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
        disabled={isGenerating || (!routerEnabled && modelId === null) || selectedLayerId === null}
        type="submit"
      >
        {isGenerating ? 'Generating...' : 'Generate'}
      </button>
    </form>
  )
}
