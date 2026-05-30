import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Project } from '../types/project'
import { ProjectList } from './ProjectList'

const initialProjects: Project[] = [
  { id: 1, name: 'Brake Controller', created_at: '2026-05-30T10:00:00' },
  { id: 2, name: 'Sensor Module', created_at: '2026-05-30T10:01:00' },
]

type ProjectPayload = {
  name: string
}

function jsonResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body,
  } as Response
}

function projectRow(projectName: string): HTMLElement {
  const row = screen.getByText(projectName).closest('li')
  if (row === null) {
    throw new Error(`Missing row for ${projectName}`)
  }
  return row
}

describe('ProjectList', () => {
  let projects: Project[]
  let nextProjectId: number

  beforeEach(() => {
    projects = [...initialProjects]
    nextProjectId = 3

    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const path = input.toString()
        const method = init?.method ?? 'GET'

        if (path === '/api/projects' && method === 'GET') {
          return jsonResponse(projects)
        }

        if (path === '/api/projects' && method === 'POST') {
          const payload = JSON.parse(String(init?.body)) as ProjectPayload
          const project = {
            id: nextProjectId,
            name: payload.name,
            created_at: '2026-05-30T10:02:00',
          }
          nextProjectId += 1
          projects = [...projects, project]
          return jsonResponse(project)
        }

        if (path.startsWith('/api/projects/') && method === 'PATCH') {
          const projectId = Number(path.replace('/api/projects/', ''))
          const payload = JSON.parse(String(init?.body)) as ProjectPayload
          const renamedProject = projects.find((project) => project.id === projectId)
          if (renamedProject === undefined) {
            return { ok: false, status: 404, json: async () => ({}) } as Response
          }
          projects = projects.map((project) =>
            project.id === projectId ? { ...project, name: payload.name } : project,
          )
          return jsonResponse({ ...renamedProject, name: payload.name })
        }

        if (path.startsWith('/api/projects/') && method === 'DELETE') {
          const projectId = Number(path.replace('/api/projects/', ''))
          projects = projects.filter((project) => project.id !== projectId)
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

  it('renders projects loaded from the API', async () => {
    render(<ProjectList />)

    expect(await screen.findByText('Brake Controller')).toBeInTheDocument()
    expect(screen.getByText('Sensor Module')).toBeInTheDocument()
  })

  it('creates, renames, deletes, and highlights projects', async () => {
    render(<ProjectList />)

    expect(await screen.findByText('Brake Controller')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Project name'), { target: { value: 'Alpha' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add' }))

    expect(await screen.findByText('Alpha')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/projects',
      expect.objectContaining({ method: 'POST' }),
    )
    expect(projectRow('Alpha')).toHaveClass('border-neutral-950')

    fireEvent.click(within(projectRow('Alpha')).getByRole('button', { name: 'Rename' }))
    fireEvent.change(screen.getByLabelText('Rename Alpha'), { target: { value: 'Gamma' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    expect(await screen.findByText('Gamma')).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/projects/3',
      expect.objectContaining({ method: 'PATCH' }),
    )

    fireEvent.click(screen.getByText('Sensor Module'))
    expect(projectRow('Sensor Module')).toHaveClass('border-neutral-950')

    fireEvent.click(within(projectRow('Gamma')).getByRole('button', { name: 'Delete' }))

    await waitFor(() => expect(screen.queryByText('Gamma')).not.toBeInTheDocument())
    expect(fetch).toHaveBeenCalledWith('/api/projects/3', { method: 'DELETE' })
  })
})
