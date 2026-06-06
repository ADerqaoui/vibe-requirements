import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { SpecHistoryPanel } from './SpecHistoryPanel'

function response(body: unknown): Response {
  return { ok: true, json: async () => body } as Response
}

describe('SpecHistoryPanel', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lists read-only revisions with labels, timestamps, text, and status snapshots', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
        expect(input.toString()).toBe('/api/specs/4/revisions')
        return response([
          {
            revision_number: 1,
            text: 'Original text',
            status: 'pending',
            source: 'ai',
            change_type: 'created',
            created_at: '2026-06-06 10:00:00',
          },
          {
            revision_number: 2,
            text: 'Edited text',
            status: 'accepted',
            source: 'manual',
            change_type: 'status_changed',
            created_at: '2026-06-06 10:05:00',
          },
        ])
      }),
    )

    render(<SpecHistoryPanel specId={4} onClose={vi.fn()} />)

    expect(await screen.findByText('1. Created')).toBeInTheDocument()
    expect(screen.getByText('2. Status changed')).toBeInTheDocument()
    expect(screen.getByText('2026-06-06 10:00:00')).toBeInTheDocument()
    expect(screen.getByText('Original text')).toBeInTheDocument()
    expect(screen.getByText('Edited text')).toBeInTheDocument()
    expect(screen.getByText('accepted')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument()
  })
})
