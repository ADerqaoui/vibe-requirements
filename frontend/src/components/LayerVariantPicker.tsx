import type { Layer } from '../types/layer'

type LayerVariantPickerProps = {
  layers: Layer[]
  value: number | ''
  onChange: (layerId: number | '') => void
}

export function LayerVariantPicker({ layers, value, onChange }: LayerVariantPickerProps) {
  return (
    <label className="block text-xs font-medium text-neutral-700">
      Layer
      <select
        className="mt-1 w-full rounded border border-neutral-300 px-2 py-1 text-sm"
        value={value}
        onChange={(event) => onChange(event.target.value === '' ? '' : Number(event.target.value))}
      >
        <option value="">Choose layer</option>
        {layers.map((layer) => (
          <option key={layer.id} value={layer.id}>
            {layer.name}
          </option>
        ))}
      </select>
    </label>
  )
}
