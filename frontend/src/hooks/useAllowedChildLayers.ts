import { useEffect, useState } from 'react'
import { fetchAllowedChildLayers } from '../api/layers'
import { parentKey, type GenerationParent } from '../types/generationParent'
import type { Layer } from '../types/layer'

type UseAllowedChildLayersResult = {
  allowedLayers: Layer[]
  selectedLayerId: number | null
  setSelectedLayerId: (layerId: number) => void
}

export function useAllowedChildLayers(
  parent: GenerationParent | null,
  onError: (error: unknown) => void,
): UseAllowedChildLayersResult {
  const [allowedLayers, setAllowedLayers] = useState<Layer[]>([])
  const [selectedLayerId, setSelectedLayerId] = useState<number | null>(null)
  const selectedParentKey = parentKey(parent)

  useEffect(() => {
    setAllowedLayers([])
    setSelectedLayerId(null)
    if (parent === null) {
      return
    }
    fetchAllowedChildLayers(parent)
      .then((layers) => {
        setAllowedLayers(layers)
        setSelectedLayerId(layers[0]?.id ?? null)
      })
      .catch(onError)
  }, [onError, selectedParentKey])

  return { allowedLayers, selectedLayerId, setSelectedLayerId }
}
