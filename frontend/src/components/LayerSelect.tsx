import type { Layer } from '../types/layer'

type LayerSelectProps = {
  layers: Layer[]
  selectedLayerId: number | null
  onLayerChange: (layerId: number) => void
}

export function LayerSelect({ layers, selectedLayerId, onLayerChange }: LayerSelectProps) {
  return (
    <label className="grid gap-1 text-xs font-medium text-neutral-600">
      Layer
      <select
        aria-label="Target layer"
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm font-normal text-neutral-900"
        disabled={layers.length === 0}
        onChange={(event) => onLayerChange(Number(event.target.value))}
        value={selectedLayerId ?? ''}
      >
        {layers.length === 0 && <option value="">No child layers</option>}
        {layers.map((layer) => (
          <option key={layer.id} value={layer.id}>
            {layer.name}
          </option>
        ))}
      </select>
    </label>
  )
}
