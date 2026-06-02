import { parseApiError } from './errors'
import type { CompletionRequest, CompletionResult } from '../types/completion'

export async function completeModel(
  modelId: number,
  payload: CompletionRequest,
): Promise<CompletionResult> {
  const response = await fetch(`/api/models/${modelId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw await parseApiError(response, `Completion request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as CompletionResult
}
