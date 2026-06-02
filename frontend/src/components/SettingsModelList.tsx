import type { Model } from '../types/model'

type SettingsModelListProps = {
  models: Model[]
  onDeleteModel: (model: Model) => void
  onToggleModel: (model: Model) => void
}

export function SettingsModelList({
  models,
  onDeleteModel,
  onToggleModel,
}: SettingsModelListProps) {
  return (
    <ul className="mt-4 space-y-2">
      {models.map((model) => (
        <li className="rounded-md border border-neutral-200 bg-white p-3" key={model.id}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-neutral-950">{model.name}</p>
              <p className="text-xs text-neutral-500">
                {model.provider} · {model.tier} · {model.cumulative_cost_sek.toFixed(2)} SEK
              </p>
            </div>
            <button className="text-xs text-neutral-700" onClick={() => onToggleModel(model)} type="button">
              {model.enabled ? 'Disable' : 'Enable'}
            </button>
            <button className="text-xs text-red-600" onClick={() => onDeleteModel(model)} type="button">
              Remove
            </button>
          </div>
        </li>
      ))}
    </ul>
  )
}
