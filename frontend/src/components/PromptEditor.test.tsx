import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Prompt } from '../types/prompt'
import { PromptEditor } from './PromptEditor'

const prompt: Prompt = {
  task: 'classify_spec',
  name: 'Classify Spec',
  description: 'Classify',
  version: 1,
  layer_id: null,
  discipline_scope: null,
  template: 'Specification: {spec_statement}',
  updated_at: '2026-06-03 10:00:00',
}

function jsonResponse(status: number, body: unknown): Response {
  return { ok: status < 400, status, json: async () => body } as Response
}

describe('PromptEditor', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('prefills template and saves a new version', async () => {
    const onSaved = vi.fn()
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, { id: 2, ...prompt, version: 2 })))

    render(<PromptEditor prompt={prompt} onCancel={vi.fn()} onSaved={onSaved} />)

    expect(screen.getByDisplayValue('Specification: {spec_statement}')).toBeInTheDocument()
    fireEvent.change(screen.getByDisplayValue('Specification: {spec_statement}'), {
      target: { value: 'Score {spec_statement}' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(onSaved).toHaveBeenCalled())
    expect(fetch).toHaveBeenCalledWith('/api/prompts/classify_spec/versions', expect.objectContaining({
      method: 'POST',
    }))
  })

  it('shows inline validation reason for 422 responses', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(422, { error: 'prompt_template_invalid', reason: 'missing variables' })),
    )

    render(<PromptEditor prompt={prompt} onCancel={vi.fn()} onSaved={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('missing variables')).toBeInTheDocument()
  })
})
