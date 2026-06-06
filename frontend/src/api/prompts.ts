import { parseApiError } from './errors'
import type {
  Prompt,
  PromptContracts,
  PromptDefaultSet,
  PromptPreviewRequest,
  PromptPreviewResponse,
  PromptVariant,
  PromptVersion,
  PromptVersionCreate,
} from '../types/prompt'

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

export async function fetchPromptVariants(task: string, layerId?: number | null): Promise<PromptVariant[]> {
  const query = layerId === undefined || layerId === null ? '' : `?layer_id=${layerId}`
  const response = await fetch(`${PROMPTS_PATH}/${encodeURIComponent(task)}/variants${query}`)
  if (!response.ok) {
    throw new Error(`Prompt variants request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as PromptVariant[]
}

export async function fetchPromptContracts(): Promise<PromptContracts> {
  const response = await fetch(`${PROMPTS_PATH}/contracts`)
  if (!response.ok) {
    throw new Error(`Prompt contracts request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as PromptContracts
}

export async function previewPrompt(payload: PromptPreviewRequest): Promise<PromptPreviewResponse> {
  const response = await fetch(`${PROMPTS_PATH}/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (response.status === 422) {
    const body = (await response.json()) as { reason?: string }
    throw new PromptTemplateInvalidApiError(body.reason ?? 'Invalid prompt template')
  }
  if (!response.ok) {
    throw await parseApiError(response, `Prompt preview failed: HTTP ${response.status}`)
  }
  return (await response.json()) as PromptPreviewResponse
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

export async function setPromptDefault(payload: PromptDefaultSet): Promise<PromptDefaultSet> {
  const response = await fetch(`${PROMPTS_PATH}/set-default`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    throw new Error(`Prompt default request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as PromptDefaultSet
}
