export type Need = {
  id: number
  project_id: number
  statement: string
  context: string | null
  constraints: string | null
  complexity: number | null
  created_at: string
  updated_at: string
}

export type NeedPayload = {
  statement: string
  context?: string
  constraints?: string
}
