export type Prompt = {
  task: string
  name: string
  description: string | null
  version: number
  layer_id: number | null
  discipline_scope: string | null
  template: string
  updated_at: string
}
