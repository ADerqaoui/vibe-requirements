import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PromptsPanel } from './PromptsPanel'

function jsonResponse(body: unknown): Response {
  return { ok: true, json: async () => body } as Response
}

describe('PromptsPanel', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders active prompts with version and template content', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse([
          {
            task: 'generate_need_to_spec',
            name: 'Generate Need to Spec',
            description: 'Generate child specifications from a Need.',
            version: 1,
            layer_id: null,
            discipline_scope: null,
            template: 'Need: {parent_statement}',
            updated_at: '2026-06-02 10:00:00',
          },
          {
            task: 'classify_spec',
            name: 'Classify Spec',
            description: null,
            version: 2,
            layer_id: 7,
            discipline_scope: 'SW',
            template: 'Specification: {spec_statement}',
            updated_at: '2026-06-02 11:00:00',
          },
        ]),
      ),
    )

    render(<PromptsPanel />)

    expect(await screen.findByText('Generate Need to Spec')).toBeInTheDocument()
    expect(screen.getByText(/generate_need_to_spec · v1 · layer any · discipline any/)).toBeInTheDocument()
    expect(screen.getByText('Need: {parent_statement}')).toBeInTheDocument()
    expect(screen.getByText('Classify Spec')).toBeInTheDocument()
    expect(screen.getByText(/classify_spec · v2 · layer 7 · discipline SW/)).toBeInTheDocument()
    expect(screen.getByText('Specification: {spec_statement}')).toBeInTheDocument()
    expect(screen.queryByText('Editable in a future slice.')).not.toBeInTheDocument()
  })

  it('refreshes active prompts after edit and promote', async () => {
    let prompt = {
      task: 'classify_spec',
      name: 'Classify Spec',
      description: null,
      version: 1,
      layer_id: null,
      discipline_scope: null,
      template: 'Specification: {spec_statement}',
      updated_at: '2026-06-03 10:00:00',
    }
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = input.toString()
        const method = init?.method ?? 'GET'
        if (path === '/api/prompts' && method === 'GET') {
          return jsonResponse([prompt])
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

    expect(await screen.findByText(/classify_spec · v1/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    expect(await screen.findByText(/classify_spec · v2/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'History' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Promote' }))

    await waitFor(() => expect(screen.getByText(/classify_spec · v1/)).toBeInTheDocument())
  })
})
