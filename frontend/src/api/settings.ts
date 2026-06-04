import type { Setting, SettingsResponse } from '../types/setting'

const SETTINGS_PATH = '/api/settings'

export async function fetchSettings(): Promise<SettingsResponse> {
  const response = await fetch(SETTINGS_PATH)
  if (!response.ok) {
    throw new Error(`Settings request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as SettingsResponse
}

export async function updateSettings(
  settings: Setting[],
  routerEnabled?: boolean,
): Promise<SettingsResponse> {
  const response = await fetch(SETTINGS_PATH, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ settings, router_enabled: routerEnabled }),
  })
  if (!response.ok) {
    throw new Error(`Settings request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as SettingsResponse
}
