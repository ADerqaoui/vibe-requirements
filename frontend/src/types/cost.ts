export type CostBreakdownByProvider = {
  provider: string
  month_sek: number
}

export type CostBreakdownByModel = {
  model_id: number
  model_name: string
  month_sek: number
}

export type CostSummary = {
  currency: 'SEK'
  ceiling_sek: number
  month_spent_sek: number
  month_remaining_sek: number
  all_time_spent_sek: number
  by_provider: CostBreakdownByProvider[]
  by_model: CostBreakdownByModel[]
}

export type CostCeilingResponse = {
  error: 'cost_ceiling_exceeded'
  spent_sek: number
  ceiling_sek: number
  currency: 'SEK'
}
