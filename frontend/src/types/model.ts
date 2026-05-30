export type Model = {
  id: number
  provider: string
  name: string
  ollama_tag: string | null
  api_model_id: string | null
  tier: string
  input_cost_per_1k: number
  output_cost_per_1k: number
  enabled: boolean
  cumulative_cost_sek: number
}

export type ModelPayload = {
  provider: string
  name: string
  ollama_tag?: string
  api_model_id?: string
  tier: string
  input_cost_per_1k?: number
  output_cost_per_1k?: number
  enabled?: boolean
}
