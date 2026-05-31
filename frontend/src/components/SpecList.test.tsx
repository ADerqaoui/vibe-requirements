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

const childSpec: Spec = {
  id: 5,
  need_id: 1,
  statement: 'The brake actuator shall clamp.',
  complexity: null,
  created_at: '2026-05-31T01:00:00',
  updated_at: '2026-05-31T01:00:00',
}

describe('SpecList', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'

        if (path === '/api/specs/4/specs' && method === 'GET') {
          return { ok: true, json: async () => [] } as Response
        }

        if (path === '/api/specs/5/specs' && method === 'GET') {
          return { ok: true, json: async () => [] } as Response
        }

        if (path === '/api/specs/4/classify' && method === 'POST') {
          return {
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
          } as Response
        }

        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
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

  it('renders nested child specs and selects a child', async () => {
    vi.mocked(fetch).mockImplementation(
      async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'
        if (path === '/api/specs/4/specs' && method === 'GET') {
          return { ok: true, json: async () => [childSpec] } as Response
        }
        if (path === '/api/specs/5/specs' && method === 'GET') {
          return { ok: true, json: async () => [] } as Response
        }
        return { ok: false, status: 500, json: async () => ({}) } as Response
      },
    )
    const onSelectSpec = vi.fn()

    render(<SpecList onSelectSpec={onSelectSpec} specs={specs} />)

    fireEvent.click(await screen.findByText('The brake actuator shall clamp.'))

    expect(onSelectSpec).toHaveBeenCalledWith(childSpec)
  })
})
