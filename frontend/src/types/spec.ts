export type Spec = {
  id: number
  need_id: number
  parent_spec_id: number | null
  statement: string
  complexity: number | null
  status: string
  latest_inspection_id: number | null
  created_at: string
  updated_at: string
}

export type SpecPayload = {
  statement: string
}

export type SpecTreeNode = {
  id: number
  statement: string
  complexity: number | null
  status: string
  parent_spec_id: number | null
  latest_inspection_id: number | null
  children: SpecTreeNode[]
}
