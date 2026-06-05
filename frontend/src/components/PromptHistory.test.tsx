import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PromptHistory } from './PromptHistory'

function jsonResponse(body: unknown): Response {
  return { ok: true, status: 200, json: async () => body } as Response
}

describe('PromptHistory', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lists versions and promotes inactive history', async () => {
    const onPromoted = vi.fn()
    const versions = [
      {
        id: 2,
        task: 'generate_spec_to_child',
        name: 'Spec child',
        description: null,
        version: 2,
        enabled: 1,
        layer_id: null,
        layer_name: null,
        discipline_scope: null,
        template: 'Parent specification: {parent_statement}',
        created_at: '2026-06-03 10:00:00',
        updated_at: '2026-06-03 10:00:00',
      },
      {
        id: 1,
        task: 'generate_spec_to_child',
        name: 'Spec child',
        description: null,
        version: 1,
        enabled: 0,
        layer_id: null,
        layer_name: null,
        discipline_scope: null,
        template: 'Need: {parent_statement}',
        created_at: '2026-06-02 10:00:00',
        updated_at: '2026-06-02 10:00:00',
      },
    ]
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(versions)))

    render(
      <PromptHistory
        task="generate_spec_to_child"
        layerId={null}
        name="Spec child"
        onClose={vi.fn()}
        onPromoted={onPromoted}
      />,
    )

    expect(await screen.findByText(/Global · v2/)).toBeInTheDocument()
    expect(screen.getByText('Need: {parent_statement}')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Promote' }))

    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/prompts/1/promote', { method: 'POST' }))
    await waitFor(() => expect(onPromoted).toHaveBeenCalled())
  })
})
