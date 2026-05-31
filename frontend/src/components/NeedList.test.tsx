import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Need } from '../types/need'
import { NeedList } from './NeedList'

const initialNeeds: Need[] = [
  {
    id: 1,
    project_id: 7,
    statement: 'Stop the vehicle',
    context: 'Wet road',
    constraints: null,
    complexity: null,
    created_at: '2026-05-30T10:00:00',
    updated_at: '2026-05-30T10:00:00',
  },
]

type NeedRequestPayload = {
  statement: string
  context?: string
  constraints?: string
}

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body,
  } as Response
}

function needRow(statement: string): HTMLElement {
  const row = screen.getByText(statement).closest('li')
  if (row === null) {
    throw new Error(`Missing row for ${statement}`)
  }
  return row
}

describe('NeedList', () => {
  let needs: Need[]
  let nextNeedId: number

  beforeEach(() => {
    needs = [...initialNeeds]
    nextNeedId = 2

    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'

        if (path === '/api/projects/7/needs' && method === 'GET') {
          return jsonResponse(needs)
        }

        if (path === '/api/models' && method === 'GET') {
          return jsonResponse([])
        }

        if (path.startsWith('/api/needs/') && path.endsWith('/specs') && method === 'GET') {
          return jsonResponse([])
        }

        if (path === '/api/projects/7/needs' && method === 'POST') {
          const payload = JSON.parse(String(init?.body)) as NeedRequestPayload
          const need = {
            id: nextNeedId,
            project_id: 7,
            statement: payload.statement,
            context: payload.context ?? null,
            constraints: payload.constraints ?? null,
            complexity: null,
            created_at: '2026-05-30T10:01:00',
            updated_at: '2026-05-30T10:01:00',
          }
          nextNeedId += 1
          needs = [...needs, need]
          return jsonResponse(need)
        }

        if (path.startsWith('/api/needs/') && method === 'PATCH') {
          const needId = Number(path.replace('/api/needs/', ''))
          const payload = JSON.parse(String(init?.body)) as NeedRequestPayload
          const currentNeed = needs.find((need) => need.id === needId)
          if (currentNeed === undefined) {
            return { ok: false, status: 404, json: async () => ({}) } as Response
          }
          const updatedNeed = {
            ...currentNeed,
            statement: payload.statement,
            context: payload.context ?? null,
            constraints: payload.constraints ?? null,
            complexity: null,
          }
          needs = needs.map((need) => (need.id === needId ? updatedNeed : need))
          return jsonResponse(updatedNeed)
        }

        if (path.startsWith('/api/needs/') && method === 'DELETE') {
          const needId = Number(path.replace('/api/needs/', ''))
          needs = needs.filter((need) => need.id !== needId)
          return { ok: true } as Response
        }

        return { ok: false, status: 500, json: async () => ({}) } as Response
      },
    )

    vi.stubGlobal('fetch', fetchMock)
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('shows selected project needs and unclassified state', async () => {
    render(<NeedList projectId={7} />)

    expect(await screen.findByText('Stop the vehicle')).toBeInTheDocument()
    expect(screen.getByText('Unclassified')).toBeInTheDocument()
  })

  it('creates, edits, deletes, prompts, and highlights needs', async () => {
    render(<NeedList projectId={7} />)

    expect(await screen.findByText('Stop the vehicle')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Need statement'), { target: { value: 'Brake safely' } })
    fireEvent.change(screen.getByLabelText('Need context'), { target: { value: 'Snow' } })
    fireEvent.change(screen.getByLabelText('Need constraints'), { target: { value: '2 seconds' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add need' }))

    expect(await screen.findByText('Brake safely')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/projects/7/needs',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(needRow('Brake safely')).toHaveClass('border-neutral-950')

    fireEvent.click(within(needRow('Brake safely')).getByRole('button', { name: 'Edit' }))
    fireEvent.change(screen.getByLabelText('Edit statement 2'), { target: { value: 'Brake firmly' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('Brake firmly')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/needs/2',
      expect.objectContaining({ method: 'PATCH' }),
    )

    fireEvent.click(screen.getByText('Stop the vehicle'))
    expect(needRow('Stop the vehicle')).toHaveClass('border-neutral-950')

    fireEvent.click(within(needRow('Brake firmly')).getByRole('button', { name: 'Delete' }))

    await waitFor(() => expect(screen.queryByText('Brake firmly')).not.toBeInTheDocument())
    expect(window.confirm).toHaveBeenCalled()
    expect(fetch).toHaveBeenCalledWith('/api/needs/2', { method: 'DELETE' })
  })
})
