import { Dispatch, SetStateAction, useCallback } from 'react'
import { CostCeilingError } from '../api/errors'

export type CostCeilingBannerState = {
  spentSek: number
  ceilingSek: number
  currency: 'SEK'
} | null

type UseCostCeilingErrorOptions = {
  setCeilingBanner: Dispatch<SetStateAction<CostCeilingBannerState>>
  setError: Dispatch<SetStateAction<string | null>>
}

export function useCostCeilingError({
  setCeilingBanner,
  setError,
}: UseCostCeilingErrorOptions) {
  return useCallback(
    (error: unknown): boolean => {
      if (!(error instanceof CostCeilingError)) {
        return false
      }
      setCeilingBanner({
        spentSek: error.spent_sek,
        ceilingSek: error.ceiling_sek,
        currency: error.currency,
      })
      setError(null)
      return true
    },
    [setCeilingBanner, setError],
  )
}
