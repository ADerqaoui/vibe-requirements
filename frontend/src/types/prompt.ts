export type Prompt = {
  task: string
  name: string
  description: string | null
  version: number
  layer_id: number | null
  layer_name: string | null
  discipline_scope: string | null
  template: string
  updated_at: string
}

export type PromptVersion = Prompt & {
  id: number
  enabled: number
  created_at: string
}

export type PromptVersionCreate = {
  template: string
  layer_id?: number | null
  name?: string
  description?: string
}
