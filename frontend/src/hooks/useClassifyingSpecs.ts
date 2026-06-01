import { useCallback, useState } from 'react'

type UseClassifyingSpecsResult = {
  addClassifyingSpecId: (specId: number) => void
  classifyingSpecIds: Set<number>
  removeClassifyingSpecId: (specId: number) => void
}

export function useClassifyingSpecs(): UseClassifyingSpecsResult {
  const [classifyingSpecIds, setClassifyingSpecIds] = useState<Set<number>>(new Set())

  const addClassifyingSpecId = useCallback((specId: number) => {
    setClassifyingSpecIds((currentIds) => new Set(currentIds).add(specId))
  }, [])

  const removeClassifyingSpecId = useCallback((specId: number) => {
    setClassifyingSpecIds((currentIds) => {
      const nextIds = new Set(currentIds)
      nextIds.delete(specId)
      return nextIds
    })
  }, [])

  return { addClassifyingSpecId, classifyingSpecIds, removeClassifyingSpecId }
}
