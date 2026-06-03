import type { Prompt, PromptVersion, PromptVersionCreate } from '../types/prompt'

const PROMPTS_PATH = '/api/prompts'

export class PromptTemplateInvalidApiError extends Error {
  reason: string

  constructor(reason: string) {
    super(reason)
    this.name = 'PromptTemplateInvalidApiError'
    this.reason = reason
  }
}

export async function fetchPrompts(): Promise<Prompt[]> {
  const response = await fetch(PROMPTS_PATH)
  if (!response.ok) {
    throw new Error(`Prompts request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Prompt[]
}

export async function fetchPromptVersions(task: string): Promise<PromptVersion[]> {
  const response = await fetch(`${PROMPTS_PATH}/${encodeURIComponent(task)}/versions`)
  if (!response.ok) {
    throw new Error(`Prompt versions request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as PromptVersion[]
}

export async function createPromptVersion(
  task: string,
  payload: PromptVersionCreate,
): Promise<PromptVersion> {
  const response = await fetch(`${PROMPTS_PATH}/${encodeURIComponent(task)}/versions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (response.status === 422) {
    const body = (await response.json()) as { reason?: string }
    throw new PromptTemplateInvalidApiError(body.reason ?? 'Invalid prompt template')
  }
  if (!response.ok) {
    throw new Error(`Prompt save failed: HTTP ${response.status}`)
  }
  return (await response.json()) as PromptVersion
}

export async function promotePromptVersion(promptId: number): Promise<PromptVersion> {
  const response = await fetch(`${PROMPTS_PATH}/${promptId}/promote`, { method: 'POST' })
  if (!response.ok) {
    throw new Error(`Prompt promote failed: HTTP ${response.status}`)
  }
  return (await response.json()) as PromptVersion
}
