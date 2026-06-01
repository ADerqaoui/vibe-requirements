import type { BlacklistEntry, BlacklistPayload } from '../types/blacklist'

export async function fetchNeedBlacklist(needId: number): Promise<BlacklistEntry[]> {
  return fetchBlacklist(`/api/needs/${needId}/blacklist`)
}

export async function fetchSpecBlacklist(specId: number): Promise<BlacklistEntry[]> {
  return fetchBlacklist(`/api/specs/${specId}/blacklist`)
}

export async function createNeedBlacklistEntry(
  needId: number,
  payload: BlacklistPayload,
): Promise<BlacklistEntry> {
  return createBlacklistEntry(`/api/needs/${needId}/blacklist`, payload)
}

export async function createSpecBlacklistEntry(
  specId: number,
  payload: BlacklistPayload,
): Promise<BlacklistEntry> {
  return createBlacklistEntry(`/api/specs/${specId}/blacklist`, payload)
}

async function fetchBlacklist(path: string): Promise<BlacklistEntry[]> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`Blacklist request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as BlacklistEntry[]
}

async function createBlacklistEntry(
  path: string,
  payload: BlacklistPayload,
): Promise<BlacklistEntry> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Blacklist request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as BlacklistEntry
}
