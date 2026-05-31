export type Spec = {
  id: number
  need_id: number
  statement: string
  complexity: number | null
  created_at: string
  updated_at: string
}

export type SpecPayload = {
  statement: string
}
