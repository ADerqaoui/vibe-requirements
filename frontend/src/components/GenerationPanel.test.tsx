import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { GenerationCandidate } from '../types/generation'
import type { Model } from '../types/model'
import type { SpecTreeNode } from '../types/spec'
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

function appendChild(
  specs: SpecTreeNode[],
  parentSpecId: number,
  child: SpecTreeNode,
): SpecTreeNode[] {
  return specs.map((spec) => {
    if (spec.id === parentSpecId) {
      return { ...spec, children: [...spec.children, child] }
    }
    return { ...spec, children: appendChild(spec.children, parentSpecId, child) }
  })
}

describe('GenerationPanel', () => {
  let specTreeByNeed: Record<number, SpecTreeNode[]>
  let candidatesByNeed: Record<number, GenerationCandidate[]>
  let candidatesBySpec: Record<number, GenerationCandidate[]>
  let classifyHandler: (specId: number) => Promise<Response> | Response
  let classifyRequests: number[]
  let requestLog: string[]

  beforeEach(() => {
    specTreeByNeed = { 1: [], 2: [] }
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
    classifyRequests = []
    requestLog = []
    classifyHandler = (specId: number) =>
      jsonResponse({ spec_id: specId, votes: [{ model_id: 3, vote: 3 }], complexity: 3 })

    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'
        requestLog.push(`${method} ${path}`)

        if (path === '/api/models' && method === 'GET') {
          return jsonResponse(models)
        }

        if (path.startsWith('/api/needs/') && path.endsWith('/spec-tree') && method === 'GET') {
          const needId = Number(path.replace('/api/needs/', '').replace('/spec-tree', ''))
          return jsonResponse(specTreeByNeed[needId] ?? [])
        }

        if (path.startsWith('/api/needs/') && path.endsWith('/generate') && method === 'POST') {
          const needId = Number(path.replace('/api/needs/', '').replace('/generate', ''))
          return jsonResponse({ candidates: candidatesByNeed[needId] ?? [] })
        }

        if (path.startsWith('/api/specs/') && path.endsWith('/generate') && method === 'POST') {
          const specId = Number(path.replace('/api/specs/', '').replace('/generate', ''))
          return jsonResponse({ candidates: candidatesBySpec[specId] ?? [] })
        }

        if (path.startsWith('/api/specs/') && path.endsWith('/classify') && method === 'POST') {
          const specId = Number(path.replace('/api/specs/', '').replace('/classify', ''))
          classifyRequests.push(specId)
          return await classifyHandler(specId)
        }

        if (path.startsWith('/api/needs/') && path.endsWith('/specs') && method === 'POST') {
          const needId = Number(path.replace('/api/needs/', '').replace('/specs', ''))
          const payload = JSON.parse(String(init?.body)) as { statement: string }
          const specs = [
            ...(specTreeByNeed[needId] ?? []),
            {
              id: 10,
              statement: payload.statement,
              complexity: null,
              status: 'pending',
              parent_spec_id: null,
              latest_inspection_id: null,
              children: [],
            },
          ]
          specTreeByNeed = { ...specTreeByNeed, [needId]: specs }
          return jsonResponse(specs[specs.length - 1])
        }

        if (path.startsWith('/api/specs/') && path.endsWith('/specs') && method === 'POST') {
          const specId = Number(path.replace('/api/specs/', '').replace('/specs', ''))
          const payload = JSON.parse(String(init?.body)) as { statement: string }
          const child: SpecTreeNode = {
            id: 30,
            statement: payload.statement,
            complexity: null,
            status: 'pending',
            parent_spec_id: specId,
            latest_inspection_id: null,
            children: [],
          }
          specTreeByNeed = { ...specTreeByNeed, 1: appendChild(specTreeByNeed[1] ?? [], specId, child) }
          return jsonResponse({
            id: child.id,
            need_id: 1,
            parent_spec_id: specId,
            statement: payload.statement,
            complexity: null,
            status: 'pending',
            latest_inspection_id: null,
            created_at: '2026-05-31T01:00:00',
            updated_at: '2026-05-31T01:00:00',
          })
        }

        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )
  })

  afterEach(() => {
    vi.restoreAllMocks()
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
    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/needs/1/spec-tree'))
    expect(await screen.findAllByText('The system shall brake.')).toHaveLength(1)

    fireEvent.click(screen.getAllByRole('button', { name: 'Reject' })[0])
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

    fireEvent.click(screen.getAllByRole('button', { name: 'Accept' })[0])
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        '/api/needs/2/specs',
        expect.objectContaining({ method: 'POST' }),
      ),
    )
  })

  it('generates and accepts child specs for a selected Spec', async () => {
    render(<GenerationPanel parent={{ kind: 'spec', id: 10 }} rootNeedId={1} />)

    expect(await screen.findByText('qwen')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The actuator shall clamp.')).toBeInTheDocument()

    fireEvent.click(screen.getAllByRole('button', { name: 'Accept' })[0])

    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        '/api/specs/10/specs',
        expect.objectContaining({ method: 'POST' }),
      ),
    )
    await waitFor(() =>
      expect(screen.queryByText('The actuator shall clamp.')).not.toBeInTheDocument(),
    )
  })

  it('keeps the full tree visible while selecting nodes and accepting a child candidate', async () => {
    specTreeByNeed = {
      1: [
        {
          id: 10,
          statement: 'Root spec',
          complexity: null,
          status: 'pending',
          parent_spec_id: null,
          latest_inspection_id: null,
          children: [
            {
              id: 20,
              statement: 'Child spec',
              complexity: null,
              status: 'pending',
              parent_spec_id: 10,
              latest_inspection_id: null,
              children: [],
            },
          ],
        },
      ],
    }
    const handleSelectSpec = vi.fn()
    const { rerender } = render(
      <GenerationPanel
        onSelectSpec={handleSelectSpec}
        parent={{ kind: 'need', id: 1 }}
        rootNeedId={1}
      />,
    )

    const rootNode = await screen.findByText('Root spec')
    const childNode = screen.getByText('Child spec')
    expect(rootNode.closest('li')).toContainElement(childNode)

    fireEvent.click(rootNode)
    expect(handleSelectSpec).toHaveBeenCalledWith(expect.objectContaining({ id: 10 }))

    rerender(
      <GenerationPanel
        onSelectSpec={handleSelectSpec}
        parent={{ kind: 'spec', id: 10 }}
        rootNeedId={1}
      />,
    )
    expect(await screen.findByText('Root spec')).toBeInTheDocument()
    expect(screen.getByText('Child spec')).toBeInTheDocument()
    expect(screen.getByText('Root spec').closest('li')).toHaveClass('border-blue-500')

    fireEvent.click(screen.getByText('Child spec'))
    expect(handleSelectSpec).toHaveBeenCalledWith(expect.objectContaining({ id: 20 }))

    rerender(
      <GenerationPanel
        onSelectSpec={handleSelectSpec}
        parent={{ kind: 'spec', id: 20 }}
        rootNeedId={1}
      />,
    )
    expect(await screen.findByText('Root spec')).toBeInTheDocument()
    expect(screen.getByText('Child spec').closest('li')).toHaveClass('border-blue-500')
    expect(screen.getByText('Root spec').closest('li')).toContainElement(screen.getByText('Child spec'))

    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The controller shall trace.')).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: 'Accept' })[0])

    await waitFor(() => expect(screen.getAllByText('The controller shall trace.')).toHaveLength(1))
    expect(screen.getByText('Child spec').closest('li')).toContainElement(
      screen.getByText('The controller shall trace.'),
    )
  })

  it('auto-classifies an accepted spec and updates the new tree node in place', async () => {
    let resolveClassify: (response: Response) => void = () => undefined
    classifyHandler = () =>
      new Promise<Response>((resolve) => {
        resolveClassify = resolve
      })

    render(<GenerationPanel needId={1} />)

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The system shall brake.')).toBeInTheDocument()

    fireEvent.click(screen.getAllByRole('button', { name: 'Accept' })[0])

    await waitFor(() => expect(screen.getAllByText('The system shall brake.')).toHaveLength(1))
    expect(await screen.findByText('Classifying...')).toBeInTheDocument()
    expect(classifyRequests).toEqual([10])
    expect(requestLog.indexOf('POST /api/needs/1/specs')).toBeLessThan(
      requestLog.indexOf('POST /api/specs/10/classify'),
    )
    expect(requestLog.filter((entry) => entry === 'GET /api/needs/1/spec-tree')).toHaveLength(2)

    resolveClassify(
      jsonResponse({ spec_id: 10, votes: [{ model_id: 3, vote: 5 }], complexity: 5 }),
    )

    await waitFor(() => expect(screen.queryByText('Classifying...')).not.toBeInTheDocument())
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(requestLog.filter((entry) => entry === 'GET /api/needs/1/spec-tree')).toHaveLength(2)
  })

  it('keeps accepted specs visible when auto-classification fails and leaves manual classify usable', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    let classifyAttempts = 0
    classifyHandler = (specId: number) => {
      classifyAttempts += 1
      if (classifyAttempts === 1) {
        return { ok: false, status: 500, json: async () => ({}) } as Response
      }
      return jsonResponse({
        spec_id: specId,
        votes: [{ model_id: 3, vote: 4 }],
        complexity: 4,
      })
    }

    render(<GenerationPanel needId={1} />)

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The system shall brake.')).toBeInTheDocument()

    fireEvent.click(screen.getAllByRole('button', { name: 'Accept' })[0])

    await waitFor(() => expect(screen.getAllByText('The system shall brake.')).toHaveLength(1))
    await waitFor(() =>
      expect(warnSpy).toHaveBeenCalledWith(
        'Auto-classify failed after accepting spec',
        expect.any(Error),
      ),
    )
    expect(screen.queryByText('Classification request failed: HTTP 500')).not.toBeInTheDocument()
    expect(screen.getByText('The system shall brake.')).toBeInTheDocument()
    expect(screen.queryByText('Classifying...')).not.toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Classify' }))

    expect(await screen.findByText('4')).toBeInTheDocument()
    expect(classifyRequests).toEqual([10, 10])
    warnSpy.mockRestore()
  })

  it('clears stale candidates on Need-Spec, Spec-Spec, and Spec-Need switches', async () => {
    const { rerender } = render(<GenerationPanel parent={{ kind: 'need', id: 1 }} rootNeedId={1} />)

    expect(await screen.findByLabelText('Generation model')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The system shall brake.')).toBeInTheDocument()

    rerender(<GenerationPanel parent={{ kind: 'spec', id: 10 }} rootNeedId={1} />)
    await waitFor(() => expect(screen.queryByText('The system shall brake.')).not.toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The actuator shall clamp.')).toBeInTheDocument()

    rerender(<GenerationPanel parent={{ kind: 'spec', id: 20 }} rootNeedId={1} />)
    await waitFor(() =>
      expect(screen.queryByText('The actuator shall clamp.')).not.toBeInTheDocument(),
    )
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The controller shall trace.')).toBeInTheDocument()

    rerender(<GenerationPanel parent={{ kind: 'need', id: 2 }} rootNeedId={2} />)
    await waitFor(() =>
      expect(screen.queryByText('The controller shall trace.')).not.toBeInTheDocument(),
    )
    fireEvent.click(screen.getByRole('button', { name: 'Generate' }))
    expect(await screen.findByText('The system shall park.')).toBeInTheDocument()
  })
})
