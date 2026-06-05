import type { ManualSpecPayload, Spec, SpecPayload, SpecTreeNode } from '../types/spec'

export async function fetchNeedSpecs(needId: number): Promise<Spec[]> {
  const response = await fetch(`/api/needs/${needId}/specs`)
  if (!response.ok) {
    throw new Error(`Specs request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec[]
}

export async function fetchNeedSpecTree(needId: number): Promise<SpecTreeNode[]> {
  const response = await fetch(`/api/needs/${needId}/spec-tree`)
  if (!response.ok) {
    throw new Error(`Spec tree request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as SpecTreeNode[]
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

export async function createManualNeedSpec(needId: number, payload: ManualSpecPayload): Promise<Spec> {
  const response = await fetch(`/api/needs/${needId}/specs/manual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Manual spec request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec
}

export async function createManualChildSpec(specId: number, payload: ManualSpecPayload): Promise<Spec> {
  const response = await fetch(`/api/specs/${specId}/specs/manual`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Manual spec request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec
}

export async function updateSpecText(specId: number, text: string): Promise<Spec> {
  const response = await fetch(`/api/specs/${specId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!response.ok) {
    throw new Error(`Spec edit request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec
}
