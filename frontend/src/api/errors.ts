import type { CostCeilingResponse } from '../types/cost'

export class CostCeilingError extends Error {
  spent_sek: number
  ceiling_sek: number
  currency: 'SEK'

  constructor(body: CostCeilingResponse) {
    super(`Cost ceiling reached — ${body.spent_sek.toFixed(2)} / ${body.ceiling_sek.toFixed(2)} SEK this month.`)
    this.name = 'CostCeilingError'
    this.spent_sek = body.spent_sek
    this.ceiling_sek = body.ceiling_sek
    this.currency = body.currency
  }
}

type ErrorBody = {
  detail?: string
  error?: string
  spent_sek?: number
  ceiling_sek?: number
  currency?: string
}

export async function parseApiError(response: Response, fallback: string): Promise<Error> {
  const body = (await response.json().catch(() => ({}))) as ErrorBody
  if (
    response.status === 402 &&
    body.error === 'cost_ceiling_exceeded' &&
    typeof body.spent_sek === 'number' &&
    typeof body.ceiling_sek === 'number' &&
    body.currency === 'SEK'
  ) {
    return new CostCeilingError(body as CostCeilingResponse)
  }
  return new Error(body.detail ?? fallback)
}

export function costCeilingMessage(error: CostCeilingError): string {
  return `Cost ceiling reached — ${error.spent_sek.toFixed(2)} / ${error.ceiling_sek.toFixed(2)} ${error.currency} this month. Raise it in Settings or use a local model.`
}
