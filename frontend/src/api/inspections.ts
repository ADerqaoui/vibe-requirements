import { parseApiError } from './errors'
import type { SpecInspection } from '../types/inspection'

export async function inspectSpec(specId: number, modelId?: number): Promise<SpecInspection> {
  const response = await fetch(`/api/specs/${specId}/inspect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(modelId === undefined ? {} : { model_id: modelId }),
  })
  if (!response.ok) {
    throw await parseApiError(response, `Inspection request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as SpecInspection
}

export async function fetchSpecInspections(specId: number): Promise<SpecInspection[]> {
  const response = await fetch(`/api/specs/${specId}/inspections`)
  if (!response.ok) {
    throw new Error(`Inspection list request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as SpecInspection[]
}
