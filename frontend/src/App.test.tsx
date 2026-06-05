import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'

function jsonResponse(body: unknown): Response {
  return { ok: true, json: async () => body } as Response
}

const settings = [
  { key: 'fx_rate_usd_sek', value: '11.0' },
  { key: 'complexity_tier_map', value: '1-2:low,3:mid,4-5:high' },
  { key: 'router_default', value: 'off' },
  { key: 'cost_ceiling_sek', value: '50' },
]

describe('App router setting flow', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('updates generation and inspection model choice immediately after settings toggle', async () => {
    let routerEnabled = false
    const requestBodies: string[] = []
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'
        if (path === '/api/settings' && method === 'GET') {
          return jsonResponse({ settings, provider_keys: {}, router_enabled: routerEnabled })
        }
        if (path === '/api/settings' && method === 'PUT') {
          routerEnabled = Boolean(JSON.parse(String(init?.body)).router_enabled)
          return jsonResponse({ settings, provider_keys: {}, router_enabled: routerEnabled })
        }
        if (path === '/api/projects') {
          return jsonResponse([{ id: 1, name: 'Demo', created_at: 'now' }])
        }
        if (path === '/api/projects/1/needs') {
          return jsonResponse([{ id: 1, project_id: 1, statement: 'Need', created_at: 'now', updated_at: 'now' }])
        }
        if (path === '/api/models') {
          return jsonResponse([
            {
              id: 3,
              name: 'qwen',
              provider: 'ollama',
              ollama_tag: 'qwen',
              api_model_id: null,
              tier: 'mid',
              input_cost_per_1k: 0,
              output_cost_per_1k: 0,
              enabled: true,
              cumulative_cost_sek: 0,
            },
          ])
        }
        if (path === '/api/layers/allowed-children?parent_kind=need') {
          return jsonResponse([{ id: 2, name: 'System Requirement', kind: 'cross_cutting', discipline: null, sort_order: 10 }])
        }
        if (path === '/api/needs/1/spec-tree') {
          return jsonResponse([
            {
              id: 4,
              statement: 'Spec',
              complexity: null,
              status: 'pending',
              parent_spec_id: null,
              layer_id: 2,
              layer_name: 'System Requirement',
              latest_inspection_id: null,
              children: [],
            },
          ])
        }
        if (path === '/api/needs/1/blacklist' || path === '/api/prompts' || path === '/api/layers') {
          return jsonResponse([])
        }
        if (path.includes('/api/prompts/') && path.includes('/variants')) {
          return jsonResponse([{
            name: 'Default',
            version: 1,
            template: 'Prompt',
            is_default: true,
            prompt_id: 9,
            layer_id: null,
            layer_name: null,
            scope_label: 'Global',
          }])
        }
        if (path === '/api/cost-summary') {
          return jsonResponse({ currency: 'SEK', ceiling_sek: 50, month_spent_sek: 0, month_remaining_sek: 50, all_time_spent_sek: 0, by_provider: [], by_model: [] })
        }
        if (path === '/api/needs/1/generate' || path === '/api/specs/4/inspect') {
          requestBodies.push(String(init?.body))
          return jsonResponse(
            path.endsWith('/generate')
              ? { candidates: [], selected_model_id: 3, selected_model_name: 'qwen' }
              : { id: 8, spec_id: 4, model_id: 3, selected_model_id: 3, selected_model_name: 'qwen', passes: 1, created_at: 'now', findings: { summary: null, criteria: [] } },
          )
        }
        return { ok: true, json: async () => ({}) } as Response
      }),
    )

    render(<App />)

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    expect(await screen.findByLabelText('Inspection model')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('checkbox', { name: /Router/ }))

    expect(await screen.findAllByText('Auto (router)')).toHaveLength(2)
    expect(await screen.findAllByText(/Auto \(default\)/)).toHaveLength(2)
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    fireEvent.click(screen.getByRole('button', { name: 'Inspect' }))
    expect(requestBodies.every((body) => !body.includes('model_id'))).toBe(true)
    expect(requestBodies.every((body) => !body.includes('prompt_id'))).toBe(true)

    fireEvent.click(screen.getByRole('checkbox', { name: /Router/ }))

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    expect(await screen.findByLabelText('Inspection model')).toBeInTheDocument()
  })
})
