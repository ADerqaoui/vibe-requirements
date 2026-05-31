export type CompletionRequest = {
  prompt: string
  system?: string
}

export type CompletionResult = {
  text: string
  in_tokens: number
  out_tokens: number
  cost_sek: number
  duration_ms: number
}
