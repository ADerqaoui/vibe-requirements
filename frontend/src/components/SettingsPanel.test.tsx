import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Model } from '../types/model'
import type { Setting, SettingsResponse } from '../types/setting'
import { SettingsPanel } from './SettingsPanel'

const initialModels: Model[] = [
  {
    id: 1,
    provider: 'ollama',
    name: 'qwen2.5:7b',
    ollama_tag: 'qwen2.5:7b',
    api_model_id: null,
    tier: 'mid',
    input_cost_per_1k: 0,
    output_cost_per_1k: 0,
    enabled: true,
    cumulative_cost_sek: 0,
  },
]

const initialSettings: SettingsResponse = {
  settings: [
    { key: 'fx_rate_usd_sek', value: '11.0' },
    { key: 'complexity_tier_map', value: '1-2:low,3:mid,4-5:high' },
    { key: 'router_default', value: 'off' },
    { key: 'cost_ceiling_sek', value: '50' },
  ],
  provider_keys: {
    anthropic: 'configured',
    openai: 'not_configured',
    deepseek: 'not_configured',
  },
  router_enabled: false,
}

type ModelPayload = {
  provider: string
  name: string
  tier: string
  enabled?: boolean
}

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body,
  } as Response
}

function modelRow(name: string): HTMLElement {
  const row = screen.getByText(name).closest('li')
  if (row === null) {
    throw new Error(`Missing row for ${name}`)
  }
  return row
}

describe('SettingsPanel', () => {
  let models: Model[]
  let settings: SettingsResponse
  let nextModelId: number

  beforeEach(() => {
    models = [...initialModels]
    settings = { ...initialSettings, settings: [...initialSettings.settings] }
    nextModelId = 2

    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'

        if (path === '/api/models' && method === 'GET') {
          return jsonResponse(models)
        }

        if (path === '/api/settings' && method === 'GET') {
          return jsonResponse(settings)
        }

        if (path === '/api/cost-summary' && method === 'GET') {
          return jsonResponse({
            currency: 'SEK',
            ceiling_sek: 50,
            month_spent_sek: 12.34,
            month_remaining_sek: 37.66,
            all_time_spent_sek: 18.21,
            by_provider: [{ provider: 'openai', month_sek: 8 }],
            by_model: [{ model_id: 7, model_name: 'gpt', month_sek: 8 }],
          })
        }

        if (path === '/api/prompts' && method === 'GET') {
          return jsonResponse([])
        }

        if (path === '/api/models' && method === 'POST') {
          const payload = JSON.parse(String(init?.body)) as ModelPayload
          const model: Model = {
            id: nextModelId,
            provider: payload.provider,
            name: payload.name,
            ollama_tag: null,
            api_model_id: null,
            tier: payload.tier,
            input_cost_per_1k: 0,
            output_cost_per_1k: 0,
            enabled: payload.enabled ?? false,
            cumulative_cost_sek: 0,
          }
          nextModelId += 1
          models = [...models, model]
          return jsonResponse(model)
        }

        if (path.startsWith('/api/models/') && method === 'PATCH') {
          const modelId = Number(path.replace('/api/models/', ''))
          models = models.map((model) =>
            model.id === modelId ? { ...model, enabled: !model.enabled } : model,
          )
          return jsonResponse(models.find((model) => model.id === modelId))
        }

        if (path.startsWith('/api/models/') && method === 'DELETE') {
          const modelId = Number(path.replace('/api/models/', ''))
          models = models.filter((model) => model.id !== modelId)
          return { ok: true } as Response
        }

        if (path === '/api/settings' && method === 'PUT') {
          const payload = JSON.parse(String(init?.body)) as { settings: Setting[]; router_enabled?: boolean }
          settings = {
            ...settings,
            settings: payload.settings,
            router_enabled: payload.router_enabled ?? settings.router_enabled,
          }
          return jsonResponse(settings)
        }

        return { ok: false, status: 500, json: async () => ({}) } as Response
      },
    )

    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lists models, settings, and masked key statuses', async () => {
    render(<SettingsPanel />)

    expect(await screen.findByText('qwen2.5:7b')).toBeInTheDocument()
    expect(await screen.findByText('12.34 / 50.00 SEK this month')).toBeInTheDocument()
    expect(screen.getByDisplayValue('11.0')).toBeInTheDocument()
    expect(screen.getByText('anthropic: configured')).toBeInTheDocument()
  })

  it('adds, toggles, removes models, and edits settings', async () => {
    render(<SettingsPanel />)

    expect(await screen.findByText('qwen2.5:7b')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Model name'), { target: { value: 'Custom GPT' } })
    fireEvent.change(screen.getByLabelText('Model provider'), { target: { value: 'openai' } })
    fireEvent.change(screen.getByLabelText('Model tier'), { target: { value: 'high' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add model' }))

    expect(await screen.findByText('Custom GPT')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith('/api/models', expect.objectContaining({ method: 'POST' }))

    fireEvent.click(within(modelRow('Custom GPT')).getByRole('button', { name: 'Enable' }))
    expect(fetch).toHaveBeenCalledWith('/api/models/2', expect.objectContaining({ method: 'PATCH' }))

    fireEvent.change(screen.getByLabelText('fx_rate_usd_sek'), { target: { value: '10.5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save settings' }))
    expect(fetch).toHaveBeenCalledWith('/api/settings', expect.objectContaining({ method: 'PUT' }))

    fireEvent.click(screen.getByRole('checkbox', { name: /Router/ }))
    expect(fetch).toHaveBeenCalledWith('/api/settings', expect.objectContaining({ method: 'PUT' }))

    fireEvent.click(within(modelRow('Custom GPT')).getByRole('button', { name: 'Remove' }))
    await waitFor(() => expect(screen.queryByText('Custom GPT')).not.toBeInTheDocument())
    expect(fetch).toHaveBeenCalledWith('/api/models/2', { method: 'DELETE' })
  })
})
