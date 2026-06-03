export type GenerationRequest = {
  model_id: number
  count: number
  target_layer_id: number
}

export type GenerationCandidate = {
  index: number
  statement: string
}

export type GenerationResult = {
  candidates: GenerationCandidate[]
}
