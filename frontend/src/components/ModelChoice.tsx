import type { Model } from '../types/model'

type ModelChoiceProps = {
  label: string
  ariaLabel: string
  modelId: number | null
  models: Model[]
  routerEnabled: boolean
  onModelIdChange: (modelId: number) => void
}

export function ModelChoice({
  label,
  ariaLabel,
  modelId,
  models,
  routerEnabled,
  onModelIdChange,
}: ModelChoiceProps) {
  if (routerEnabled) {
    return (
      <div className="grid gap-1 text-xs font-medium text-neutral-600">
        {label}
        <div className="rounded-md border border-neutral-300 bg-neutral-50 px-3 py-2 text-sm font-normal text-neutral-900">
          Auto (router)
        </div>
      </div>
    )
  }

  return (
    <label className="grid gap-1 text-xs font-medium text-neutral-600">
      {label}
      <select
        aria-label={ariaLabel}
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
  )
}
