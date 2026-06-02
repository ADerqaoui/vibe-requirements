type CostCeilingBannerProps = {
  spentSek: number
  ceilingSek: number
  currency: 'SEK'
}

export function CostCeilingBanner({ spentSek, ceilingSek, currency }: CostCeilingBannerProps) {
  return (
    <p className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
      Cost ceiling reached — {spentSek.toFixed(2)} / {ceilingSek.toFixed(2)} {currency} this
      month. Raise it in Settings or use a local model.
    </p>
  )
}
