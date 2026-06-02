import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { CostPanel } from './CostPanel'

function jsonResponse(body: unknown): Response {
  return { ok: true, json: async () => body } as Response
}

describe('CostPanel', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders cost summary numbers and breakdowns', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({
          currency: 'SEK',
          ceiling_sek: 50,
          month_spent_sek: 12.34,
          month_remaining_sek: 37.66,
          all_time_spent_sek: 18.21,
          by_provider: [{ provider: 'openai', month_sek: 8.1 }],
          by_model: [{ model_id: 7, model_name: 'gpt-4o-mini', month_sek: 8.1 }],
        }),
      ),
    )

    render(<CostPanel />)

    expect(await screen.findByText('12.34 / 50.00 SEK this month')).toBeInTheDocument()
    expect(screen.getByText('Remaining: 37.66 SEK · All-time: 18.21 SEK')).toBeInTheDocument()
    expect(screen.getByText('openai')).toBeInTheDocument()
    expect(screen.getByText('gpt-4o-mini')).toBeInTheDocument()
  })

  it('refetches when refreshSignal changes', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          currency: 'SEK',
          ceiling_sek: 50,
          month_spent_sek: 1,
          month_remaining_sek: 49,
          all_time_spent_sek: 1,
          by_provider: [],
          by_model: [],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          currency: 'SEK',
          ceiling_sek: 50,
          month_spent_sek: 2,
          month_remaining_sek: 48,
          all_time_spent_sek: 2,
          by_provider: [],
          by_model: [],
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    const { rerender } = render(<CostPanel refreshSignal={0} />)
    expect(await screen.findByText('1.00 / 50.00 SEK this month')).toBeInTheDocument()

    rerender(<CostPanel refreshSignal={1} />)

    expect(await screen.findByText('2.00 / 50.00 SEK this month')).toBeInTheDocument()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
  })
})
