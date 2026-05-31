import type { Spec, SpecPayload } from '../types/spec'

export async function fetchNeedSpecs(needId: number): Promise<Spec[]> {
  const response = await fetch(`/api/needs/${needId}/specs`)
  if (!response.ok) {
    throw new Error(`Specs request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec[]
}

export async function createNeedSpec(needId: number, payload: SpecPayload): Promise<Spec> {
  const response = await fetch(`/api/needs/${needId}/specs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Specs request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec
}

export async function fetchChildSpecs(specId: number): Promise<Spec[]> {
  const response = await fetch(`/api/specs/${specId}/specs`)
  if (!response.ok) {
    throw new Error(`Specs request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec[]
}

export async function createChildSpec(specId: number, payload: SpecPayload): Promise<Spec> {
  const response = await fetch(`/api/specs/${specId}/specs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Specs request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec
}
