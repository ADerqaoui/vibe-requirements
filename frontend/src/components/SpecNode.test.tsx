import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { SpecTreeNode } from '../types/spec'
import { SpecNode } from './SpecNode'

const spec: SpecTreeNode = {
  id: 4,
  req_id: 'REQ-SYS-0001',
  statement: 'The system shall brake.',
  source: 'ai',
  complexity: null,
  status: 'pending',
  parent_spec_id: null,
  layer_id: 2,
  layer_name: 'System Requirement',
  latest_inspection_id: null,
  children: [],
}

function renderNode(onSpecChanged = vi.fn()) {
  render(
    <SpecNode
      classifyingSpecIds={new Set()}
      complexityBySpec={{}}
      inspectionBySpec={{}}
      loadingInspectionId={null}
      loadingSpecId={null}
      onClassify={vi.fn()}
      onDecide={vi.fn()}
      onInspect={vi.fn()}
      onSpecChanged={onSpecChanged}
      spec={spec}
      statusBySpec={{}}
      votesBySpec={{}}
    />,
  )
}

describe('SpecNode', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders req_id and source badge', () => {
    renderNode()

    expect(screen.getByText('REQ-SYS-0001')).toBeInTheDocument()
    expect(screen.getByText('AI')).toBeInTheDocument()
  })

  it('renders the statement and actions in separate rows', () => {
    renderNode()

    const statementButton = screen.getByRole('button', { name: /REQ-SYS-0001 The system shall brake\./ })
    const acceptButton = screen.getByRole('button', { name: 'Accept' })

    expect(statementButton.parentElement).not.toBe(acceptButton.parentElement)
  })

  it('edits a spec inline and refreshes the tree', async () => {
    const onSpecChanged = vi.fn()
    vi.stubGlobal(
      'fetch',
      vi.fn(async (): Promise<Response> => ({ ok: true, json: async () => ({}) }) as Response),
    )
    renderNode(onSpecChanged)

    fireEvent.click(screen.getByRole('button', { name: 'Edit' }))
    const editor = screen.getByLabelText('Spec text')
    expect(editor).toHaveValue('The system shall brake.')
    fireEvent.change(editor, { target: { value: 'The system shall stop safely.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(onSpecChanged).toHaveBeenCalled())
    expect(fetch).toHaveBeenCalledWith(
      '/api/specs/4',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ text: 'The system shall stop safely.' }),
      }),
    )
  })

  it('opens read-only history for a spec', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (): Promise<Response> => ({
        ok: true,
        json: async () => [
          {
            revision_number: 1,
            text: 'The system shall brake.',
            status: 'pending',
            source: 'ai',
            change_type: 'created',
            created_at: '2026-06-06 10:00:00',
          },
        ],
      }) as Response),
    )
    renderNode()

    fireEvent.click(screen.getByRole('button', { name: 'History' }))

    expect(await screen.findByText('1. Created')).toBeInTheDocument()
    expect(screen.getAllByText('The system shall brake.')).toHaveLength(2)
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })
})
