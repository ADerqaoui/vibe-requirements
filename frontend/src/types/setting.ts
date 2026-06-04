export type Setting = {
  key: string
  value: string | null
}

export type SettingsResponse = {
  settings: Setting[]
  provider_keys: Record<string, 'configured' | 'not_configured'>
  router_enabled: boolean
}
