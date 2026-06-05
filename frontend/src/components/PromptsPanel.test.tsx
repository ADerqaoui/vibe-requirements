import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Prompt } from '../types/prompt'
import { PromptsPanel } from './PromptsPanel'

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response
}

const layers = [
  { id: 1, name: 'Need', kind: 'cross_cutting', discipline: null, sort_order: 0 },
  { id: 2, name: 'System Requirement', kind: 'cross_cutting', discipline: null, sort_order: 10 },
]

function variantsFor(prompt: Prompt, isDefault = true) {
  return [{ name: prompt.name, version: prompt.version, template: prompt.template, is_default: isDefault, prompt_id: prompt.version }]
}

function promptFixture(overrides: Partial<Prompt> = {}): Prompt {
  return {
    task: 'classify_spec',
    name: 'Classify Spec',
    description: null,
    version: 1,
    layer_id: null,
    layer_name: null,
    discipline_scope: null,
    template: 'Specification: {spec_statement}',
    updated_at: '2026-06-03 10:00:00',
    ...overrides,
  }
}

describe('PromptsPanel', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders active prompts with version and template content', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const path = input.toString()
        if (path === '/api/layers') {
          return jsonResponse(layers)
        }
        if (path.includes('/variants')) {
          const prompts = basePrompts()
          const prompt = path.includes('generate_need_to_spec') ? prompts[0] : prompts[1]
          return jsonResponse(variantsFor(prompt))
        }
        return jsonResponse(basePrompts())
      }),
    )

    render(<PromptsPanel />)

    expect(await screen.findByText('Generate Need to Spec')).toBeInTheDocument()
    expect(screen.getByText(/Global · v1/)).toBeInTheDocument()
    expect(screen.getByText('Need: {parent_statement}')).toBeInTheDocument()
    expect(screen.getByText('Classify Spec')).toBeInTheDocument()
    expect(screen.getByText(/System Requirement · v2/)).toBeInTheDocument()
    expect(screen.getByText('Specification: {spec_statement}')).toBeInTheDocument()
    expect(screen.queryByText('Editable in a future slice.')).not.toBeInTheDocument()
  })

  it('shows variants and sets the default', async () => {
    let earsDefault = false
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = input.toString()
        const method = init?.method ?? 'GET'
        const prompt = basePrompts()[0]
        if (path === '/api/layers') {
          return jsonResponse(layers)
        }
        if (path === '/api/prompts' && method === 'GET') {
          return jsonResponse([prompt])
        }
        if (path.includes('/variants')) {
          return jsonResponse([
            ...variantsFor(prompt, !earsDefault),
            { name: 'EARS', version: 1, template: 'EARS {parent_statement}', is_default: earsDefault, prompt_id: 99 },
          ])
        }
        if (path === '/api/prompts/set-default' && method === 'POST') {
          expect(init?.body).toContain('"name":"EARS"')
          earsDefault = true
          return jsonResponse({ task: prompt.task, layer_id: null, name: 'EARS' })
        }
        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )

    render(<PromptsPanel />)

    expect(await screen.findByText('EARS')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Set default' }))
    await waitFor(() => expect(screen.getByText(/v1 · updated .* · default/)).toBeInTheDocument())
  })

  function basePrompts(): Prompt[] {
    return [
      promptFixture({
        task: 'generate_need_to_spec',
        name: 'Generate Need to Spec',
        description: 'Generate child specifications from a Need.',
        template: 'Need: {parent_statement}',
        updated_at: '2026-06-02 10:00:00',
      }),
      promptFixture({ version: 2, layer_id: 2, layer_name: 'System Requirement', updated_at: '2026-06-02 11:00:00' }),
    ]
  }

  it('refreshes active prompts after edit and promote', async () => {
    let prompt = promptFixture()
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = input.toString()
        const method = init?.method ?? 'GET'
        if (path === '/api/prompts' && method === 'GET') {
          return jsonResponse([prompt])
        }
        if (path === '/api/layers' && method === 'GET') {
          return jsonResponse(layers)
        }
        if (path.includes('/variants') && method === 'GET') {
          return jsonResponse(variantsFor(prompt))
        }
        if (path === '/api/prompts/classify_spec/versions' && method === 'POST') {
          prompt = { ...prompt, version: 2, template: 'Score {spec_statement}' }
          return jsonResponse({ id: 2, enabled: 1, created_at: 'now', ...prompt })
        }
        if (path === '/api/prompts/classify_spec/versions' && method === 'GET') {
          return jsonResponse([
            { id: 2, enabled: 1, created_at: 'now', ...prompt },
            { id: 1, enabled: 0, created_at: 'old', ...prompt, version: 1 },
          ])
        }
        if (path === '/api/prompts/1/promote' && method === 'POST') {
          prompt = { ...prompt, version: 1, template: 'Specification: {spec_statement}' }
          return jsonResponse({ id: 1, enabled: 1, created_at: 'old', ...prompt })
        }
        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )

    render(<PromptsPanel />)

    expect(await screen.findByText(/Global · v1/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByText(/Global · v2/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'History' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Promote' }))

    await waitFor(() => expect(screen.getByText(/Global · v1/)).toBeInTheDocument())
  })

  it('adds a layer variant with a layer picker and layer_id payload', async () => {
    let prompts: Prompt[] = [promptFixture()]
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = input.toString()
        const method = init?.method ?? 'GET'
        if (path === '/api/prompts' && method === 'GET') {
          return jsonResponse(prompts)
        }
        if (path === '/api/layers' && method === 'GET') {
          return jsonResponse(layers)
        }
        if (path.includes('/variants') && method === 'GET') {
          return jsonResponse(prompts.flatMap((prompt) => variantsFor(prompt)))
        }
        if (path === '/api/prompts/classify_spec/versions' && method === 'POST') {
          expect(init?.body).toContain('"layer_id":2')
          prompts = [{ ...prompts[0], layer_id: 2, layer_name: 'System Requirement' }]
          return jsonResponse({ id: 3, enabled: 1, created_at: 'now', ...prompts[0] })
        }
        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )

    render(<PromptsPanel />)

    fireEvent.click(await screen.findByRole('button', { name: 'Add layer variant' }))
    fireEvent.change(screen.getByLabelText('Layer'), { target: { value: '2' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText(/System Requirement · v1/)).toBeInTheDocument()
  })
})
