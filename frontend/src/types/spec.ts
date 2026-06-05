export type Spec = {
  id: number
  need_id: number
  parent_spec_id: number | null
  layer_id: number
  layer_name: string
  req_id: string | null
  statement: string
  source: string
  complexity: number | null
  status: string
  latest_inspection_id: number | null
  created_at: string
  updated_at: string
}

export type SpecPayload = {
  statement: string
  target_layer_id: number
}

export type ManualSpecPayload = {
  text: string
  target_layer_id: number
}

export type SpecTreeNode = {
  id: number
  req_id?: string | null
  statement: string
  source?: string
  complexity: number | null
  status: string
  parent_spec_id: number | null
  layer_id: number
  layer_name: string
  latest_inspection_id: number | null
  children: SpecTreeNode[]
}
