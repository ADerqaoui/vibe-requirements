type SettingsProviderKeysProps = {
  providerKeys: Record<string, string>
}

export function SettingsProviderKeys({ providerKeys }: SettingsProviderKeysProps) {
  return (
    <ul className="mt-2 space-y-1 text-sm text-neutral-700">
      {Object.entries(providerKeys).map(([provider, status]) => (
        <li key={provider}>
          {provider}: {status}
        </li>
      ))}
    </ul>
  )
}
