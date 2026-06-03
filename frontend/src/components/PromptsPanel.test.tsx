import { render, screen } from '@testing-library/react'
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
    expect(screen.getByText('Editable in a future slice.')).toBeInTheDocument()
  })
})
