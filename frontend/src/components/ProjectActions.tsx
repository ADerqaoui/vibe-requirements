import { useState } from 'react'
import { fetchProjectMarkdown } from '../api/export'

type ProjectActionsProps = {
  projectId: number | null
  projectName: string | null
}

function slugify(value: string): string {
  const normalizedValue = value
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
  return normalizedValue === '' ? 'project' : normalizedValue
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function ProjectActions({ projectId, projectName }: ProjectActionsProps) {
  const [error, setError] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)

  async function handleExport() {
    if (projectId === null || projectName === null) {
      return
    }
    setIsExporting(true)
    try {
      const blob = await fetchProjectMarkdown(projectId)
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${slugify(projectName)}.md`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
      setError(null)
    } catch (exportError: unknown) {
      setError(errorMessage(exportError))
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <div className="mt-3">
      <button
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm text-neutral-900 disabled:text-neutral-400"
        disabled={projectId === null || isExporting}
        onClick={handleExport}
        type="button"
      >
        {isExporting ? 'Exporting...' : 'Export Markdown'}
      </button>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  )
}
