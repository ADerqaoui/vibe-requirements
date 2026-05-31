export type BlacklistEntry = {
  id: number
  parent_need_id: number | null
  parent_spec_id: number | null
  text: string
  source: string
  created_at: string
}

export type BlacklistPayload = {
  statement: string
}
