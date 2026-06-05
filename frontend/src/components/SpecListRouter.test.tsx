import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { SpecTreeNode } from '../types/spec'
import { SpecList } from './SpecList'

const specs: SpecTreeNode[] = [
  {
    id: 4,
    req_id: 'REQ-SYS-0001',
    statement: 'The system shall brake.',
    source: 'ai',
    complexity: null,
    status: 'pending',
    parent_spec_id: null,
    layer_id: 2,
    layer_name: 'System Requirement',
    latest_inspection_id: null,
    children: [],
  },
]

describe('SpecList router mode', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('omits model_id and shows selected inspection model', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        if (path === '/api/models') {
          return { ok: true, json: async () => [] } as Response
        }
        if (path === '/api/specs/4/inspect') {
          expect(String(init?.body)).toBe('{}')
          return {
            ok: true,
            json: async () => ({
              id: 9,
              spec_id: 4,
              model_id: 7,
              selected_model_id: 7,
              selected_model_name: 'high-router',
              passes: 1,
              created_at: '2026-05-31T01:00:00',
              findings: { summary: null, criteria: [{ name: 'Clarity', verdict: 'PASS', note: 'clear' }] },
            }),
          } as Response
        }
        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )

    render(<SpecList routerEnabled specs={specs} />)

    expect(await screen.findByText('Auto (router)')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Inspect' }))

    expect(await screen.findByText('Inspected with: high-router')).toBeInTheDocument()
  })
})
