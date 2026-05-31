import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { GenerationCandidate } from '../types/generation'
import type { Model } from '../types/model'
import type { Spec } from '../types/spec'
import { GenerationPanel } from './GenerationPanel'

const models: Model[] = [
  {
    id: 3,
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

function jsonResponse(body: unknown): Response {
  return { ok: true, json: async () => body } as Response
}

describe('GenerationPanel', () => {
  let specsByNeed: Record<number, Spec[]>
  let specsBySpec: Record<number, Spec[]>
  let candidatesByNeed: Record<number, GenerationCandidate[]>
  let candidatesBySpec: Record<number, GenerationCandidate[]>

  beforeEach(() => {
    specsByNeed = { 1: [], 2: [] }
    specsBySpec = { 10: [], 20: [] }
    candidatesByNeed = {
      1: [
        { index: 1, statement: 'The system shall brake.' },
        { index: 2, statement: 'The system shall alert.' },
      ],
      2: [{ index: 1, statement: 'The system shall park.' }],
    }
    candidatesBySpec = {
      10: [{ index: 1, statement: 'The actuator shall clamp.' }],
      20: [{ index: 1, statement: 'The controller shall trace.' }],
    }

    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'

        if (path === '/api/models' && method === 'GET') {
          return jsonResponse(models)
        }

        if (path.startsWith('/api/needs/') && path.endsWith('/specs') && method === 'GET') {
          const needId = Number(path.replace('/api/needs/', '').replace('/specs', ''))
          return jsonResponse(specsByNeed[needId] ?? [])
        }

        if (path.startsWith('/api/needs/') && path.endsWith('/generate') && method === 'POST') {
          const needId = Number(path.replace('/api/needs/', '').replace('/generate', ''))
          return jsonResponse({ candidates: candidatesByNeed[needId] ?? [] })
        }

        if (path.startsWith('/api/specs/') && path.endsWith('/generate') && method === 'POST') {
          const specId = Number(path.replace('/api/specs/', '').replace('/generate', ''))
          return jsonResponse({ candidates: candidatesBySpec[specId] ?? [] })
        }

        if (path.startsWith('/api/needs/') && path.endsWith('/specs') && method === 'POST') {
          const needId = Number(path.replace('/api/needs/', '').replace('/specs', ''))
          const payload = JSON.parse(String(init?.body)) as { statement: string }
          const specs = [
            ...(specsByNeed[needId] ?? []),
            {
              id: 10,
              need_id: needId,
              statement: payload.statement,
              complexity: null,
              created_at: '2026-05-31T01:00:00',
              updated_at: '2026-05-31T01:00:00',
            },
          ]
          specsByNeed = { ...specsByNeed, [needId]: specs }
          return jsonResponse(specs[specs.length - 1])
        }

        if (path.startsWith('/api/specs/') && path.endsWith('/specs') && method === 'GET') {
          const specId = Number(path.replace('/api/specs/', '').replace('/specs', ''))
          return jsonResponse(specsBySpec[specId] ?? [])
        }

        if (path.startsWith('/api/specs/') && path.endsWith('/specs') && method === 'POST') {
          const specId = Number(path.replace('/api/specs/', '').replace('/specs', ''))
          const payload = JSON.parse(String(init?.body)) as { statement: string }
          const specs = [
            ...(specsBySpec[specId] ?? []),
            {
              id: 30,
              need_id: 1,
              statement: payload.statement,
              complexity: null,
              created_at: '2026-05-31T01:00:00',
              updated_at: '2026-05-31T01:00:00',
            },
          ]
          specsBySpec = { ...specsBySpec, [specId]: specs }
          return jsonResponse(specs[specs.length - 1])
        }

        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('generates candidates, accepts one, refetches specs, and rejects one', async () => {
    render(<GenerationPanel needId={1} />)

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Generation count'), { target: { value: '2' } })
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))

    expect(await screen.findByText('The system shall brake.')).toBeInTheDocument()
    expect(screen.getByText('The system shall alert.')).toBeInTheDocument()

    fireEvent.click(screen.getAllByRole('button', { name: 'Accept' })[0])
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/needs/1/specs'))
    expect(await screen.findAllByText('The system shall brake.')).toHaveLength(1)

    fireEvent.click(screen.getByRole('button', { name: 'Reject' }))
    await waitFor(() => expect(screen.queryByText('The system shall alert.')).not.toBeInTheDocument())
  })

  it('clears stale candidates when the selected Need changes', async () => {
    const { rerender } = render(<GenerationPanel needId={1} />)

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The system shall brake.')).toBeInTheDocument()

    rerender(<GenerationPanel needId={2} />)

    await waitFor(() => expect(screen.queryByText('The system shall brake.')).not.toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The system shall park.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Accept' }))
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        '/api/needs/2/specs',
        expect.objectContaining({ method: 'POST' }),
      ),
    )
  })

  it('generates and accepts child specs for a selected Spec', async () => {
    render(<GenerationPanel parent={{ kind: 'spec', id: 10 }} />)

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The actuator shall clamp.')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Accept' }))

    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        '/api/specs/10/specs',
        expect.objectContaining({ method: 'POST' }),
      ),
    )
    expect(await screen.findAllByText('The actuator shall clamp.')).toHaveLength(1)
  })

  it('clears stale candidates on Need-Spec, Spec-Spec, and Spec-Need switches', async () => {
    const { rerender } = render(<GenerationPanel parent={{ kind: 'need', id: 1 }} />)

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The system shall brake.')).toBeInTheDocument()

    rerender(<GenerationPanel parent={{ kind: 'spec', id: 10 }} />)
    await waitFor(() => expect(screen.queryByText('The system shall brake.')).not.toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The actuator shall clamp.')).toBeInTheDocument()

    rerender(<GenerationPanel parent={{ kind: 'spec', id: 20 }} />)
    await waitFor(() =>
      expect(screen.queryByText('The actuator shall clamp.')).not.toBeInTheDocument(),
    )
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The controller shall trace.')).toBeInTheDocument()

    rerender(<GenerationPanel parent={{ kind: 'need', id: 2 }} />)
    await waitFor(() =>
      expect(screen.queryByText('The controller shall trace.')).not.toBeInTheDocument(),
    )
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The system shall park.')).toBeInTheDocument()
  })
})
