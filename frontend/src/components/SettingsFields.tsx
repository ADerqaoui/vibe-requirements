type SettingsFieldsProps = {
  settingDrafts: Record<string, string>
  settingKeys: string[]
  onSaveSettings: () => void
  onSettingDraftsChange: (settingDrafts: Record<string, string>) => void
}

export function SettingsFields({
  settingDrafts,
  settingKeys,
  onSaveSettings,
  onSettingDraftsChange,
}: SettingsFieldsProps) {
  return (
    <div className="mt-3 grid gap-2">
      {settingKeys.map((key) => (
        <label className="grid gap-1 text-xs font-medium text-neutral-600" key={key}>
          {key}
          <input
            aria-label={key}
            className="rounded-md border border-neutral-300 px-3 py-2 text-sm font-normal text-neutral-900"
            onChange={(event) =>
              onSettingDraftsChange({ ...settingDrafts, [key]: event.target.value })
            }
            value={settingDrafts[key] ?? ''}
          />
        </label>
      ))}
      <button className="w-fit rounded-md bg-neutral-950 px-3 py-2 text-sm text-white" onClick={onSaveSettings} type="button">
        Save settings
      </button>
    </div>
  )
}
