import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Spec } from '../types/spec'
import { SpecList } from './SpecList'

const specs: Spec[] = [
  {
    id: 4,
    need_id: 1,
    statement: 'The system shall brake.',
    complexity: null,
    created_at: '2026-05-31T01:00:00',
    updated_at: '2026-05-31T01:00:00',
  },
]

describe('SpecList', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
          spec_id: 4,
          complexity: 3,
          votes: [
            { model_id: 10, vote: 2 },
            { model_id: 11, vote: 3 },
            { model_id: 12, vote: 5 },
          ],
        }),
      })),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('classifies a spec and renders complexity with vote tooltip', async () => {
    render(<SpecList specs={specs} />)

    expect(screen.getByText('—')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Classify' }))

    const badge = await screen.findByText('3')
    expect(badge).toHaveAttribute('title', 'Model 10: 2\nModel 11: 3\nModel 12: 5')
    expect(fetch).toHaveBeenCalledWith('/api/specs/4/classify', { method: 'POST' })
  })
})
