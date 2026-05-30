import type { Need, NeedPayload } from '../types/need'

async function parseNeedResponse(response: Response): Promise<Need> {
  if (!response.ok) {
    throw new Error(`Needs request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Need
}

export async function fetchProjectNeeds(projectId: number): Promise<Need[]> {
  const response = await fetch(`/api/projects/${projectId}/needs`)
  if (!response.ok) {
    throw new Error(`Needs request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Need[]
}

export async function createNeed(projectId: number, payload: NeedPayload): Promise<Need> {
  const response = await fetch(`/api/projects/${projectId}/needs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseNeedResponse(response)
}

export async function updateNeed(needId: number, payload: Partial<NeedPayload>): Promise<Need> {
  const response = await fetch(`/api/needs/${needId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseNeedResponse(response)
}

export async function deleteNeed(needId: number): Promise<void> {
  const response = await fetch(`/api/needs/${needId}`, { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(`Needs request failed: HTTP ${response.status}`)
  }
}
