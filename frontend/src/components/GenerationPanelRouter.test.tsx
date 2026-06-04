import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { GenerationPanel } from './GenerationPanel'

const systemRequirement = {
  id: 2,
  name: 'System Requirement',
  kind: 'cross_cutting',
  discipline: null,
  sort_order: 10,
}

function jsonResponse(body: unknown): Response {
  return { ok: true, json: async () => body } as Response
}

describe('GenerationPanel router mode', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('omits model_id and shows selected router model', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'
        if (path === '/api/models') {
          return jsonResponse([])
        }
        if (path === '/api/settings') {
          return jsonResponse({ settings: [], provider_keys: {}, router_enabled: true })
        }
        if (path === '/api/layers/allowed-children?parent_kind=need') {
          return jsonResponse([systemRequirement])
        }
        if (path === '/api/needs/1/spec-tree' || path === '/api/needs/1/blacklist') {
          return jsonResponse([])
        }
        if (path === '/api/needs/1/generate' && method === 'POST') {
          expect(String(init?.body)).not.toContain('model_id')
          return jsonResponse({
            candidates: [{ index: 1, statement: 'The system shall brake.' }],
            selected_model_id: 7,
            selected_model_name: 'router-mid',
          })
        }
        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )

    render(<GenerationPanel rootNeedId={1} />)

    expect(await screen.findByText('Auto (router)')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))

    expect(await screen.findByText('Generated with: router-mid')).toBeInTheDocument()
  })
})
