import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Need } from '../types/need'
import { NeedRow } from './NeedRow'

const need: Need = {
  id: 1,
  project_id: 7,
  statement: 'Stop the vehicle',
  context: 'Wet road',
  constraints: null,
  complexity: null,
  created_at: '2026-05-30T10:00:00',
  updated_at: '2026-05-30T10:00:00',
}

function renderNeedRow(isSelected = true) {
  const props = {
    editDraft: { statement: '', context: '', constraints: '' },
    isEditing: false,
    isSelected,
    need,
    onBeginEdit: vi.fn(),
    onDelete: vi.fn(),
    onEditDraftChange: vi.fn(),
    onSave: vi.fn(),
    onSelect: vi.fn(),
  }
  const result = render(<NeedRow {...props} />)
  return { ...result, props }
}

describe('NeedRow', () => {
  it('keeps the pre-split rendered DOM shape for a selected Need row', () => {
    renderNeedRow()

    const row = screen.getByText('Stop the vehicle').closest('li')
    expect(row).toHaveClass('rounded-md border bg-white p-3 border-blue-500 border-l-4 bg-blue-50 font-medium')
    expect(within(row as HTMLElement).getByText('Wet road')).toHaveClass('block text-xs text-neutral-500')
    expect(within(row as HTMLElement).getByText('Unclassified')).toHaveClass(
      'mt-2 inline-block rounded bg-amber-100 px-2 py-1 text-xs text-amber-800',
    )
    expect(within(row as HTMLElement).getByRole('button', { name: 'Edit' })).toHaveClass('text-xs text-neutral-500')
    expect(within(row as HTMLElement).getByRole('button', { name: 'Delete' })).toHaveClass('text-xs text-red-600')
  })

  it('wires the row actions through props', () => {
    const { props } = renderNeedRow(false)

    fireEvent.click(screen.getByText('Stop the vehicle'))
    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }))

    expect(props.onSelect).toHaveBeenCalledWith(1)
    expect(props.onBeginEdit).toHaveBeenCalledWith(need)
    expect(props.onDelete).toHaveBeenCalledWith(need)
  })
})
