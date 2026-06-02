import { parseApiError } from './errors'
import type { CostSummary } from '../types/cost'

export async function fetchCostSummary(): Promise<CostSummary> {
  const response = await fetch('/api/cost-summary')
  if (!response.ok) {
    throw await parseApiError(response, `Cost summary request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as CostSummary
}
