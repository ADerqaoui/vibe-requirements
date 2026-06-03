import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { LayerSelect } from './LayerSelect'

const layers = [
  {
    id: 3,
    name: 'System Architecture',
    kind: 'cross_cutting',
    discipline: null,
    sort_order: 20,
  },
  {
    id: 4,
    name: 'SW Requirement',
    kind: 'discipline_locked',
    discipline: 'SW',
    sort_order: 30,
  },
]

describe('LayerSelect', () => {
  it('lists allowed child layers and reports the selected layer', () => {
    const onLayerChange = vi.fn()

    render(
      <LayerSelect layers={layers} onLayerChange={onLayerChange} selectedLayerId={3} />,
    )

    expect(screen.getByRole('option', { name: 'System Architecture' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'SW Requirement' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Target layer'), { target: { value: '4' } })

    expect(onLayerChange).toHaveBeenCalledWith(4)
  })
})
