import type { Project } from '../types/project'

const PROJECTS_PATH = '/api/projects'

async function parseProjectResponse(response: Response): Promise<Project> {
  if (!response.ok) {
    throw new Error(`Projects request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Project
}

export async function fetchProjects(): Promise<Project[]> {
  const response = await fetch(PROJECTS_PATH)
  if (!response.ok) {
    throw new Error(`Projects request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Project[]
}

export async function createProject(name: string): Promise<Project> {
  const response = await fetch(PROJECTS_PATH, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  return parseProjectResponse(response)
}

export async function renameProject(projectId: number, name: string): Promise<Project> {
  const response = await fetch(`${PROJECTS_PATH}/${projectId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  return parseProjectResponse(response)
}

export async function deleteProject(projectId: number): Promise<void> {
  const response = await fetch(`${PROJECTS_PATH}/${projectId}`, { method: 'DELETE' })
  if (!response.ok) {
    throw new Error(`Projects request failed: HTTP ${response.status}`)
  }
}
