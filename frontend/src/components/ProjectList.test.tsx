import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ProjectList } from './ProjectList'

const projects = [
  { id: 1, name: 'Brake Controller', created_at: '2026-05-30T10:00:00' },
  { id: 2, name: 'Sensor Module', created_at: '2026-05-30T10:01:00' },
]

describe('ProjectList', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => projects,
      }),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders projects loaded from the API', async () => {
    render(<ProjectList />)

    expect(await screen.findByText('Brake Controller')).toBeInTheDocument()
    expect(screen.getByText('Sensor Module')).toBeInTheDocument()
  })
})
