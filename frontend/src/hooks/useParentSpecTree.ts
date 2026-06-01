import { useCallback, useState } from 'react'
import { fetchNeedSpecTree } from '../api/specs'
import type { SpecTreeNode } from '../types/spec'

type UseParentSpecTreeResult = {
  clearSpecTree: () => void
  loadSpecTree: (needId: number) => Promise<void>
  setSpecComplexity: (specId: number, complexity: number) => void
  specs: SpecTreeNode[]
}

export function useParentSpecTree(): UseParentSpecTreeResult {
  const [specs, setSpecs] = useState<SpecTreeNode[]>([])

  const clearSpecTree = useCallback(() => setSpecs([]), [])

  const loadSpecTree = useCallback(async (needId: number) => {
    const loadedSpecs = await fetchNeedSpecTree(needId)
    setSpecs(loadedSpecs)
  }, [])

  const setSpecComplexity = useCallback((specId: number, complexity: number) => {
    setSpecs((currentSpecs) => updateSpecComplexity(currentSpecs, specId, complexity))
  }, [])

  return {
    clearSpecTree,
    loadSpecTree,
    setSpecComplexity,
    specs,
  }
}

function updateSpecComplexity(
  specs: SpecTreeNode[],
  specId: number,
  complexity: number,
): SpecTreeNode[] {
  return specs.map((spec) => {
    if (spec.id === specId) {
      return { ...spec, complexity }
    }
    return { ...spec, children: updateSpecComplexity(spec.children, specId, complexity) }
  })
}
