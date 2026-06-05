import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ManualSpecForm } from './ManualSpecForm'

function okJson(body: unknown): Response {
  return { ok: true, json: async () => body } as Response
}

describe('ManualSpecForm', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('posts a manual Need spec with the default allowed layer', async () => {
    const onCreated = vi.fn()
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        if (path === '/api/layers/allowed-children?parent_kind=need') {
          return okJson([
            { id: 2, name: 'System Requirement', kind: 'cross_cutting', discipline: null, sort_order: 10 },
          ])
        }
        if (path === '/api/needs/1/specs/manual') {
          expect(init?.body).toBe(JSON.stringify({ text: 'Manual requirement', target_layer_id: 2 }))
          return okJson({ id: 10, source: 'manual', status: 'accepted', req_id: 'REQ-SYS-0001' })
        }
        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )

    render(<ManualSpecForm onCancel={vi.fn()} onCreated={onCreated} parent={{ kind: 'need', id: 1 }} />)

    expect(await screen.findByLabelText('Manual requirement layer')).toHaveValue('2')
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Manual requirement text'), {
      target: { value: ' Manual requirement ' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(onCreated).toHaveBeenCalled())
  })

  it('posts a manual child spec for a Spec parent', async () => {
    const onCreated = vi.fn()
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        if (path === '/api/layers/allowed-children?parent_layer_id=2') {
          return okJson([
            { id: 3, name: 'System Architecture', kind: 'cross_cutting', discipline: null, sort_order: 20 },
          ])
        }
        if (path === '/api/specs/4/specs/manual') {
          expect(init?.body).toBe(JSON.stringify({ text: 'Manual child', target_layer_id: 3 }))
          return okJson({ id: 11, source: 'manual', status: 'accepted', req_id: 'REQ-SYSA-0001' })
        }
        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )

    render(
      <ManualSpecForm
        onCancel={vi.fn()}
        onCreated={onCreated}
        parent={{ kind: 'spec', id: 4, layer_id: 2 }}
      />,
    )

    expect(await screen.findByLabelText('Manual requirement layer')).toHaveValue('3')
    fireEvent.change(screen.getByLabelText('Manual requirement text'), { target: { value: 'Manual child' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(onCreated).toHaveBeenCalled())
  })
})
