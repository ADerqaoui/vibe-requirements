import { FormEvent, useEffect, useState } from 'react'
import {
  createProject,
  deleteProject,
  fetchProjects,
  renameProject,
} from '../api/projects'
import type { Project } from '../types/project'
import { ProjectActions } from './ProjectActions'

type ProjectListProps = {
  selectedProjectId: number | null
  onSelectProject: (projectId: number | null) => void
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function ProjectList({ selectedProjectId, onSelectProject }: ProjectListProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [draftName, setDraftName] = useState('')
  const [renamingProjectId, setRenamingProjectId] = useState<number | null>(null)
  const [renameDraft, setRenameDraft] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchProjects()
      .then((loadedProjects) => {
        setProjects(loadedProjects)
        onSelectProject(loadedProjects[0]?.id ?? null)
      })
      .catch((loadError: unknown) => setError(toErrorMessage(loadError)))
      .finally(() => setIsLoading(false))
  }, [onSelectProject])

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const name = draftName.trim()
    if (name.length === 0) {
      return
    }
    try {
      const project = await createProject(name)
      setProjects((currentProjects) => [...currentProjects, project])
      onSelectProject(project.id)
      setDraftName('')
      setError(null)
    } catch (createError: unknown) {
      setError(toErrorMessage(createError))
    }
  }

  async function handleRenameProject(projectId: number) {
    const name = renameDraft.trim()
    if (name.length === 0) {
      return
    }
    try {
      const renamedProject = await renameProject(projectId, name)
      setProjects((currentProjects) =>
        currentProjects.map((project) => (project.id === projectId ? renamedProject : project)),
      )
      setRenamingProjectId(null)
      setRenameDraft('')
      setError(null)
    } catch (renameError: unknown) {
      setError(toErrorMessage(renameError))
    }
  }

  async function handleDeleteProject(project: Project) {
    if (!window.confirm(`Delete project "${project.name}"?`)) {
      return
    }
    try {
      await deleteProject(project.id)
      setProjects((currentProjects) => currentProjects.filter((item) => item.id !== project.id))
      if (selectedProjectId === project.id) {
        onSelectProject(null)
      }
      setError(null)
    } catch (deleteError: unknown) {
      setError(toErrorMessage(deleteError))
    }
  }

  function beginRename(project: Project) {
    setRenamingProjectId(project.id)
    setRenameDraft(project.name)
  }

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? null

  return (
    <aside className="h-screen w-full max-w-sm border-r border-neutral-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-neutral-950">Projects</h1>
          <p className="text-sm text-neutral-500">Requirement Review Dashboard</p>
        </div>
      </div>
      <ProjectActions projectId={selectedProject?.id ?? null} projectName={selectedProject?.name ?? null} />

      <form className="mt-4 flex gap-2" onSubmit={handleCreateProject}>
        <input
          aria-label="Project name"
          className="min-w-0 flex-1 rounded-md border border-neutral-300 px-3 py-2 text-sm"
          onChange={(event) => setDraftName(event.target.value)}
          placeholder="New project"
          value={draftName}
        />
        <button className="rounded-md bg-neutral-950 px-3 py-2 text-sm text-white" type="submit">
          Add
        </button>
      </form>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {isLoading && <p className="mt-6 text-sm text-neutral-500">Loading projects...</p>}
      {!isLoading && projects.length === 0 && (
        <p className="mt-6 text-sm text-neutral-500">No projects yet.</p>
      )}

      <ul className="mt-4 space-y-2">
        {projects.map((project) => {
          const isSelected = selectedProjectId === project.id
          const isRenaming = renamingProjectId === project.id
          return (
            <li
              className={`rounded-md border p-3 ${
                isSelected ? 'border-neutral-950 bg-neutral-100' : 'border-neutral-200'
              }`}
              key={project.id}
            >
              {isRenaming ? (
                <div className="flex gap-2">
                  <input
                    aria-label={`Rename ${project.name}`}
                    className="min-w-0 flex-1 rounded-md border border-neutral-300 px-2 py-1 text-sm"
                    onChange={(event) => setRenameDraft(event.target.value)}
                    value={renameDraft}
                  />
                  <button
                    className="text-sm font-medium text-neutral-900"
                    onClick={() => handleRenameProject(project.id)}
                    type="button"
                  >
                    Save
                  </button>
                </div>
              ) : (
                <div className="flex items-center justify-between gap-2">
                  <button
                    className="min-w-0 flex-1 truncate text-left text-sm font-medium"
                    onClick={() => onSelectProject(project.id)}
                    type="button"
                  >
                    {project.name}
                  </button>
                  <button
                    className="text-xs text-neutral-500"
                    onClick={() => beginRename(project)}
                    type="button"
                  >
                    Rename
                  </button>
                  <button
                    className="text-xs text-red-600"
                    onClick={() => handleDeleteProject(project)}
                    type="button"
                  >
                    Delete
                  </button>
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </aside>
  )
}
