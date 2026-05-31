import type { GenerationRequest, GenerationResult } from '../types/generation'

export async function generateSpecs(
  needId: number,
  payload: GenerationRequest,
): Promise<GenerationResult> {
  const response = await fetch(`/api/needs/${needId}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Generation request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as GenerationResult
}
