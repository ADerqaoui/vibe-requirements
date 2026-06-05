import type { PromptVariant } from '../types/prompt'

type PromptVariantSelectProps = {
  label: string
  ariaLabel: string
  promptId: number | null
  variants: PromptVariant[]
  routerEnabled: boolean
  onPromptIdChange: (promptId: number) => void
}

function labelFor(variant: PromptVariant): string {
  const suffix = variant.is_default ? ' (default)' : ''
  return `${variant.scope_label}: ${variant.name} v${variant.version}${suffix}`
}

export function PromptVariantSelect({
  label,
  ariaLabel,
  promptId,
  variants,
  routerEnabled,
  onPromptIdChange,
}: PromptVariantSelectProps) {
  if (routerEnabled) {
    const defaultVariant = variants.find((variant) => variant.is_default) ?? variants[0]
    return (
      <div className="grid gap-1 text-xs font-medium text-neutral-600">
        {label}
        <div className="rounded-md border border-neutral-300 bg-neutral-50 px-3 py-2 text-sm font-normal text-neutral-900">
          {defaultVariant ? `Auto (default): ${labelFor(defaultVariant)}` : 'Auto (default)'}
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
        disabled={variants.length === 0}
        onChange={(event) => onPromptIdChange(Number(event.target.value))}
        value={promptId ?? ''}
      >
        {variants.length === 0 && <option value="">No prompt variants</option>}
        {variants.map((variant) => (
          <option key={variant.prompt_id} value={variant.prompt_id}>
            {labelFor(variant)}
          </option>
        ))}
      </select>
    </label>
  )
}
