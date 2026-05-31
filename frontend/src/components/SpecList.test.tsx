import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { SpecTreeNode } from '../types/spec'
import { SpecList } from './SpecList'

const childSpec: SpecTreeNode = {
  id: 5,
  statement: 'The brake actuator shall clamp.',
  complexity: null,
  status: 'pending',
  parent_spec_id: 4,
  children: [],
}

const specs: SpecTreeNode[] = [
  {
    id: 4,
    statement: 'The system shall brake.',
    complexity: null,
    status: 'pending',
    parent_spec_id: null,
    children: [childSpec],
  },
]

describe('SpecList', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'

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

    expect(screen.getAllByText('—')).toHaveLength(2)
    fireEvent.click(screen.getAllByRole('button', { name: 'Classify' })[0])

    const badge = await screen.findByText('3')
    expect(badge).toHaveAttribute('title', 'Model 10: 2\nModel 11: 3\nModel 12: 5')
    expect(fetch).toHaveBeenCalledWith('/api/specs/4/classify', { method: 'POST' })
  })

  it('renders nested child specs and selects a child', async () => {
    const onSelectSpec = vi.fn()

    render(<SpecList onSelectSpec={onSelectSpec} specs={specs} />)

    fireEvent.click(screen.getByText('The brake actuator shall clamp.'))

    expect(onSelectSpec).toHaveBeenCalledWith(childSpec)
  })
})
