import { useEffect, useState } from 'react'
import { fetchCostSummary } from '../api/cost'
import type { CostSummary } from '../types/cost'

type CostPanelProps = {
  refreshSignal?: number
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

function formatSek(value: number): string {
  return value.toFixed(2)
}

function percent(summary: CostSummary): number {
  if (summary.ceiling_sek <= 0) {
    return summary.month_spent_sek > 0 ? 100 : 0
  }
  return Math.min(100, (summary.month_spent_sek / summary.ceiling_sek) * 100)
}

export function CostPanel({ refreshSignal = 0 }: CostPanelProps) {
  const [summary, setSummary] = useState<CostSummary | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let didCancel = false
    fetchCostSummary()
      .then((loadedSummary) => {
        if (didCancel) {
          return
        }
        setSummary(loadedSummary)
        setError(null)
      })
      .catch((loadError: unknown) => {
        if (!didCancel) {
          setError(toErrorMessage(loadError))
        }
      })
    return () => {
      didCancel = true
    }
  }, [refreshSignal])

  if (summary === null) {
    return (
      <section className="rounded-md border border-neutral-200 bg-white p-3">
        <h3 className="text-sm font-semibold text-neutral-900">Cost</h3>
        {error ? (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        ) : (
          <p className="mt-2 text-sm text-neutral-500">Loading cost summary...</p>
        )}
      </section>
    )
  }

  const isReached = summary.month_spent_sek >= summary.ceiling_sek

  return (
    <section className="rounded-md border border-neutral-200 bg-white p-3">
      <h3 className="text-sm font-semibold text-neutral-900">Cost</h3>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <p className="mt-2 text-sm font-medium text-neutral-950">
        {formatSek(summary.month_spent_sek)} / {formatSek(summary.ceiling_sek)} SEK this month
      </p>
      <div className="mt-2 h-2 overflow-hidden rounded bg-neutral-100">
        <div
          aria-label="Monthly cost progress"
          className="h-full bg-neutral-900"
          style={{ width: `${percent(summary)}%` }}
        />
      </div>
      {isReached && (
        <p className="mt-2 text-sm text-amber-700">
          Cost ceiling reached. Raise it or use a local model.
        </p>
      )}
      <p className="mt-3 text-sm text-neutral-700">
        Remaining: {formatSek(summary.month_remaining_sek)} SEK · All-time:{' '}
        {formatSek(summary.all_time_spent_sek)} SEK
      </p>

      <div className="mt-3 grid gap-3 text-sm md:grid-cols-2">
        <div>
          <h4 className="text-xs font-semibold uppercase text-neutral-500">By provider</h4>
          {summary.by_provider.length === 0 ? (
            <p className="mt-1 text-neutral-500">No paid spend this month.</p>
          ) : (
            <ul className="mt-1 space-y-1">
              {summary.by_provider.map((item) => (
                <li className="flex justify-between gap-3" key={item.provider}>
                  <span>{item.provider}</span>
                  <span>{formatSek(item.month_sek)} SEK</span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <h4 className="text-xs font-semibold uppercase text-neutral-500">By model</h4>
          {summary.by_model.length === 0 ? (
            <p className="mt-1 text-neutral-500">No paid model spend this month.</p>
          ) : (
            <ul className="mt-1 space-y-1">
              {summary.by_model.map((item) => (
                <li className="flex justify-between gap-3" key={item.model_id}>
                  <span>{item.model_name}</span>
                  <span>{formatSek(item.month_sek)} SEK</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}
