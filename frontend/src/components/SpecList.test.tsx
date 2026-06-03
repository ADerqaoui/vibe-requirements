import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { SpecTreeNode } from '../types/spec'
import { SpecList } from './SpecList'

const childSpec: SpecTreeNode = {
  id: 5,
  statement: 'The brake actuator shall clamp.',
  complexity: null,
  status: 'pending',
  parent_spec_id: 4,
  layer_id: 3,
  layer_name: 'System Architecture',
  latest_inspection_id: null,
  children: [],
}

const specs: SpecTreeNode[] = [
  {
    id: 4,
    statement: 'The system shall brake.',
    complexity: null,
    status: 'pending',
    parent_spec_id: null,
    layer_id: 2,
    layer_name: 'System Requirement',
    latest_inspection_id: null,
    children: [childSpec],
  },
]

describe('SpecList', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'

        if (path === '/api/models' && method === 'GET') {
          return {
            ok: true,
            json: async () => [
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
            ],
          } as Response
        }

        if (path === '/api/specs/4/classify' && method === 'POST') {
          return {
            ok: true,
            json: async () => ({
              spec_id: 4,
              complexity: 3,
              votes: [
                { model_id: 10, vote: 2 },
                { model_id: 11, vote: 3 },
                { model_id: 12, vote: 5 },
              ],
            }),
          } as Response
        }

        if (path === '/api/specs/4/inspect' && method === 'POST') {
          return {
            ok: true,
            json: async () => ({
              id: 9,
              spec_id: 4,
              model_id: 3,
              passes: 1,
              created_at: '2026-05-31T01:00:00',
              findings: {
                summary: null,
                criteria: [
                  { name: 'Clarity', verdict: 'PASS', note: 'clear' },
                  { name: 'Measurability', verdict: 'FAIL', note: 'missing threshold' },
                ],
              },
            }),
          } as Response
        }

        if (path === '/api/specs/4/decision' && method === 'POST') {
          const payload = JSON.parse(String(init?.body)) as { decision: string }
          return {
            ok: true,
            json: async () => ({
              id: 4,
              need_id: 1,
              parent_spec_id: null,
              latest_inspection_id: 9,
              statement: 'The system shall brake.',
              complexity: null,
              status: payload.decision,
              layer_id: 2,
              layer_name: 'System Requirement',
              created_at: '2026-05-31T01:00:00',
              updated_at: '2026-05-31T01:01:00',
            }),
          } as Response
        }

        return { ok: false, status: 500, json: async () => ({}) } as Response
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('classifies a spec and renders complexity with vote tooltip', async () => {
    render(<SpecList specs={specs} />)

    expect(screen.getAllByText('—')).toHaveLength(2)
    fireEvent.click(screen.getAllByRole('button', { name: 'Classify' })[0])

    const badge = await screen.findByText('3')
    expect(badge).toHaveAttribute('title', 'Model 10: 2\nModel 11: 3\nModel 12: 5')
    expect(fetch).toHaveBeenCalledWith('/api/specs/4/classify', { method: 'POST' })
  })

  it('renders nested child specs and selects a child', async () => {
    const onSelectSpec = vi.fn()

    render(<SpecList onSelectSpec={onSelectSpec} specs={specs} />)

    expect(await screen.findByLabelText('Inspection model')).toBeInTheDocument()
    expect(screen.getByText('System Requirement')).toBeInTheDocument()
    expect(screen.getByText('System Architecture')).toBeInTheDocument()
    fireEvent.click(screen.getByText('The brake actuator shall clamp.'))

    expect(onSelectSpec).toHaveBeenCalledWith(childSpec)
  })

  it('inspects a spec, renders findings, and updates decision badge', async () => {
    const onSpecChanged = vi.fn()
    render(<SpecList onSpecChanged={onSpecChanged} specs={specs} />)

    expect(await screen.findByLabelText('Inspection model')).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: 'Inspect' })[0])

    expect(await screen.findByText('Clarity')).toBeInTheDocument()
    expect(screen.getByText('PASS')).toBeInTheDocument()
    expect(screen.getByText('missing threshold')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/specs/4/inspect',
      expect.objectContaining({ method: 'POST' }),
    )

    fireEvent.click(screen.getAllByRole('button', { name: 'Accept' })[0])

    expect(await screen.findByText('accepted')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/specs/4/decision',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(onSpecChanged).toHaveBeenCalled()
  })
})
