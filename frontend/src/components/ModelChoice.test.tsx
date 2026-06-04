import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Model } from '../types/model'
import { ModelChoice } from './ModelChoice'

const models: Model[] = [
  {
    id: 1,
    provider: 'ollama',
    name: 'qwen',
    ollama_tag: 'qwen',
    api_model_id: null,
    tier: 'mid',
    input_cost_per_1k: 0,
    output_cost_per_1k: 0,
    enabled: true,
    cumulative_cost_sek: 0,
  },
]

describe('ModelChoice', () => {
  it('renders manual model dropdown when router is off', () => {
    const onModelIdChange = vi.fn()

    render(
      <ModelChoice
        ariaLabel="Generation model"
        label="Model"
        modelId={1}
        models={models}
        onModelIdChange={onModelIdChange}
        routerEnabled={false}
      />,
    )

    fireEvent.change(screen.getByLabelText('Generation model'), { target: { value: '1' } })

    expect(screen.getByText('qwen')).toBeInTheDocument()
    expect(onModelIdChange).toHaveBeenCalledWith(1)
  })

  it('renders auto router indicator when router is on', () => {
    render(
      <ModelChoice
        ariaLabel="Generation model"
        label="Model"
        modelId={1}
        models={models}
        onModelIdChange={vi.fn()}
        routerEnabled
      />,
    )

    expect(screen.getByText('Auto (router)')).toBeInTheDocument()
    expect(screen.queryByLabelText('Generation model')).not.toBeInTheDocument()
  })
})
