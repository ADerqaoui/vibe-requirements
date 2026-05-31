import type { Spec } from '../types/spec'

export type SpecDecision = 'accepted' | 'rejected'

export async function decideSpec(specId: number, decision: SpecDecision): Promise<Spec> {
  const response = await fetch(`/api/specs/${specId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision }),
  })
  if (!response.ok) {
    throw new Error(`Decision request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Spec
}
