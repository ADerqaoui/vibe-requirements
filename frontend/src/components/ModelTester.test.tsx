import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Model } from '../types/model'
import { ModelTester } from './ModelTester'

const models: Model[] = [
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

describe('ModelTester', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
          text: 'model response',
          in_tokens: 4,
          out_tokens: 8,
          cost_sek: 0,
          duration_ms: 25,
        }),
      })),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends a prompt and displays response, tokens, cost, and duration', async () => {
    render(<ModelTester models={models} />)

    fireEvent.change(screen.getByLabelText('Test prompt'), { target: { value: 'Say hello' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))

    expect(await screen.findByText('model response')).toBeInTheDocument()
    expect(screen.getByText(/4 input tokens/)).toBeInTheDocument()
    expect(screen.getByText(/8 output tokens/)).toBeInTheDocument()
    expect(screen.getByText(/0.0000 SEK/)).toBeInTheDocument()
    expect(screen.getByText(/25 ms/)).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/models/1/complete',
      expect.objectContaining({ method: 'POST' }),
    )
  })
})
