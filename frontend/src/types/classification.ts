export type ClassificationVote = {
  model_id: number
  vote: number
}

export type ClassificationResult = {
  spec_id: number
  votes: ClassificationVote[]
  complexity: number
}
