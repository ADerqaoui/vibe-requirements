export async function fetchProjectMarkdown(projectId: number): Promise<Blob> {
  const response = await fetch(`/api/projects/${projectId}/export.md`)
  if (!response.ok) {
    throw new Error(`Export request failed: HTTP ${response.status}`)
  }
  return response.blob()
}
