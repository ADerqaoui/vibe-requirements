import { parseApiError } from './errors'
import type { ClassificationResult } from '../types/classification'

export async function classifySpec(specId: number): Promise<ClassificationResult> {
  const response = await fetch(`/api/specs/${specId}/classify`, { method: 'POST' })
  if (!response.ok) {
    throw await parseApiError(response, `Classification request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as ClassificationResult
}

export default classifySpec
