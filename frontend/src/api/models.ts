import type { Model, ModelPayload } from '../types/model'

const MODELS_PATH = '/api/models'

async function parseModelResponse(response: Response): Promise<Model> {
  if (!response.ok) {
    throw new Error(`Models request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Model
}

export async function fetchModels(): Promise<Model[]> {
  const response = await fetch(MODELS_PATH)
  if (!response.ok) {
    throw new Error(`Models request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Model[]
}

export async function createModel(payload: ModelPayload): Promise<Model> {
  const response = await fetch(MODELS_PATH, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseModelResponse(response)
}

export async function updateModel(modelId: number, payload: Partial<ModelPayload>): Promise<Model> {
  const response = await fetch(`${MODELS_PATH}/${modelId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseModelResponse(response)
}

export async function deleteModel(modelId: number): Promise<void> {
  const response = await fetch(`${MODELS_PATH}/${modelId}`, { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(`Models request failed: HTTP ${response.status}`)
  }
}
