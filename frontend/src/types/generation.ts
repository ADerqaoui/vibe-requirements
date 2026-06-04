export type GenerationRequest = {
  model_id?: number
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
}
