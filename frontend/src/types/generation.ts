export type GenerationRequest = {
  model_id?: number
  prompt_id?: number
  count: number
  target_layer_id: number
}

export type GenerationCandidate = {
  index: number
  statement: string
}

export type GenerationResult = {
  candidates: GenerationCandidate[]
  selected_model_id: number
  selected_model_name: string
  selected_prompt_id: number
  selected_prompt_name: string
}
