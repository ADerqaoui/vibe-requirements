import type { Layer } from '../types/layer'
import type { GenerationParent } from '../types/generationParent'

export async function fetchAllowedChildLayers(parent: GenerationParent): Promise<Layer[]> {
  const query =
    parent.kind === 'need'
      ? 'parent_kind=need'
      : `parent_layer_id=${encodeURIComponent(String(parent.layer_id))}`
  const response = await fetch(`/api/layers/allowed-children?${query}`)
  if (!response.ok) {
    throw new Error(`Allowed layers request failed: HTTP ${response.status}`)
  }
  return (await response.json()) as Layer[]
}
