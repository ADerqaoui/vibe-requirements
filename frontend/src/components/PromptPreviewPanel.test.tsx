import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Model } from '../types/model'
import { PromptPreviewPanel } from './PromptPreviewPanel'

const model: Model = {
  id: 7,
  provider: 'ollama',
  name: 'qwen',
  ollama_tag: 'qwen',
  api_model_id: null,
  tier: 'mid',
  input_cost_per_1k: 0,
  output_cost_per_1k: 0,
  enabled: true,
  cumulative_cost_sek: 0,
}

function response(status: number, body: unknown): Response {
  return { ok: status < 400, status, json: async () => body } as Response
}

describe('PromptPreviewPanel', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders fields by task and runs the current draft template', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        if (path === '/api/prompts/contracts') {
          return response(200, { classify_spec: ['spec_statement'] })
        }
        if (path === '/api/models') {
          return response(200, [model])
        }
        if (path === '/api/prompts/preview') {
          const payload = JSON.parse(String(init?.body)) as { template: string; variables: Record<string, string> }
          expect(payload.template).toBe('Draft {spec_statement}')
          expect(payload.variables.spec_statement).toBe('Draft sample')
          return response(200, {
            rendered_prompt: 'Draft Draft sample',
            output: 'Preview output',
            model_id: model.id,
            model_name: model.name,
            cost_sek: 0.12,
          })
        }
        return response(404, {})
      }),
    )

    render(<PromptPreviewPanel task="classify_spec" template="Draft {spec_statement}" />)

    const input = await screen.findByLabelText('spec_statement')
    fireEvent.change(input, { target: { value: 'Draft sample' } })
    fireEvent.click(screen.getByRole('button', { name: 'Run preview' }))

    expect(await screen.findByText('Draft Draft sample')).toBeInTheDocument()
    expect(screen.getByText('Preview output')).toBeInTheDocument()
    expect(screen.getByText('qwen - 0.12 SEK')).toBeInTheDocument()
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/prompts/preview', expect.any(Object)))
  })

  it('shows invalid template reasons inline', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
        const path = input.toString()
        if (path === '/api/prompts/contracts') {
          return response(200, { classify_spec: ['spec_statement'] })
        }
        if (path === '/api/models') {
          return response(200, [model])
        }
        if (path === '/api/prompts/preview') {
          return response(422, { error: 'prompt_template_invalid', reason: 'missing variables: spec_statement' })
        }
        return response(404, {})
      }),
    )

    render(<PromptPreviewPanel task="classify_spec" template="Broken" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Run preview' }))

    expect(await screen.findByText('missing variables: spec_statement')).toBeInTheDocument()
  })
})
