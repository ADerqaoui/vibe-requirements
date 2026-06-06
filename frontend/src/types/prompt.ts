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

export type PromptVariant = {
  name: string
  version: number
  template: string
  is_default: boolean
  prompt_id: number
  layer_id: number | null
  layer_name: string | null
  scope_label: string
}

export type PromptDefaultSet = {
  task: string
  layer_id?: number | null
  name: string
}

export type PromptContracts = Record<string, string[]>

export type PromptPreviewRequest = {
  task: string
  template: string
  variables: Record<string, string>
  model_id?: number
}

export type PromptPreviewResponse = {
  rendered_prompt: string
  output: string
  model_id: number
  model_name: string
  cost_sek: number
}
