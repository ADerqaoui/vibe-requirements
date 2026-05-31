export type GenerationRequest = {
  model_id: number
  count: number
}

export type GenerationCandidate = {
  index: number
  statement: string
}

export type GenerationResult = {
  candidates: GenerationCandidate[]
}
