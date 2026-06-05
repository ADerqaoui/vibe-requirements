export async function fetchProjectMarkdown(projectId: number, includeInspections = true): Promise<Blob> {
  const query = `include_inspections=${includeInspections ? 'true' : 'false'}`
  const response = await fetch(`/api/projects/${projectId}/export.md?${query}`)
  if (!response.ok) {
    throw new Error(`Export request failed: HTTP ${response.status}`)
  }
  return response.blob()
}
