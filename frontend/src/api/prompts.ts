import type { Prompt } from '../types/prompt'

const PROMPTS_PATH = '/api/prompts'

export async function fetchPrompts(): Promise<Prompt[]> {
  const response = await fetch(PROMPTS_PATH)
  if (!response.ok) {
    throw new Error(`Prompts request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Prompt[]
}
