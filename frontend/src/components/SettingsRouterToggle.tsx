type SettingsRouterToggleProps = {
  enabled: boolean
  onToggle: (enabled: boolean) => void
}

export function SettingsRouterToggle({ enabled, onToggle }: SettingsRouterToggleProps) {
  return (
    <label className="mt-3 flex items-start gap-2 text-sm text-neutral-700">
      <input
        checked={enabled}
        className="mt-1"
        onChange={(event) => onToggle(event.target.checked)}
        type="checkbox"
      />
      <span>
        <span className="block font-medium text-neutral-900">Router</span>
        When on, the best available model is chosen automatically per task, preferring local models.
      </span>
    </label>
  )
}
