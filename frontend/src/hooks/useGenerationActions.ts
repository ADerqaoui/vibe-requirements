import { Dispatch, FormEvent, SetStateAction, useCallback, useEffect, useState } from 'react'
import { createNeedBlacklistEntry, createSpecBlacklistEntry } from '../api/blacklist'
import classifySpec from '../api/classification'
import { generateChildSpecs, generateSpecs } from '../api/generation'
import { createChildSpec, createNeedSpec } from '../api/specs'
import type { GenerationCandidate } from '../types/generation'
import { parentKey, type GenerationParent } from '../types/generationParent'
import { errorMessage } from '../utils/errorMessage'
import { useClassifyingSpecs } from './useClassifyingSpecs'
import { useCostCeilingError, type CostCeilingBannerState } from './useCostCeilingError'
import { useParentBlacklist } from './useParentBlacklist'

type UseGenerationActionsParams = {
  clearSpecTree: () => void
  effectiveRootNeedId: number | null
  generationParent: GenerationParent | null
  loadSpecTree: (needId: number) => Promise<void>
  modelId: number | null
  onSuccessfulGeneration?: () => void
  routerEnabled: boolean
  selectedLayerId: number | null
  setCeilingBanner: Dispatch<SetStateAction<CostCeilingBannerState>>
  setError: Dispatch<SetStateAction<string | null>>
  setSpecComplexity: (specId: number, complexity: number) => void
}

type UseGenerationActionsResult = {
  allCandidatesBlocked: boolean
  blacklistCount: number
  candidates: GenerationCandidate[]
  classifyingSpecIds: Set<number>
  count: number
  handleAccept: (candidate: GenerationCandidate) => Promise<void>
  handleGenerate: (event: FormEvent<HTMLFormElement>) => Promise<void>
  handleReject: (candidate: GenerationCandidate) => Promise<void>
  isGenerating: boolean
  selectedModelName: string | null
  setCount: (count: number) => void
}

export function useGenerationActions({
  clearSpecTree,
  effectiveRootNeedId,
  generationParent,
  loadSpecTree,
  modelId,
  onSuccessfulGeneration,
  routerEnabled,
  selectedLayerId,
  setCeilingBanner,
  setError,
  setSpecComplexity,
}: UseGenerationActionsParams): UseGenerationActionsResult {
  const selectedParentKey = parentKey(generationParent)
  const [count, setCount] = useState(5)
  const [candidates, setCandidates] = useState<GenerationCandidate[]>([])
  const [allCandidatesBlocked, setAllCandidatesBlocked] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedModelName, setSelectedModelName] = useState<string | null>(null)
  const handleCostCeilingError = useCostCeilingError({ setCeilingBanner, setError })
  const { blacklistCount, loadBlacklistCount } = useParentBlacklist()
  const { addClassifyingSpecId, classifyingSpecIds, removeClassifyingSpecId } = useClassifyingSpecs()

  const handleLoadSpecTreeError = useCallback((unknownError: unknown) => {
    setError(errorMessage(unknownError))
  }, [])

  useEffect(() => {
    clearSpecTree()
    setCandidates([])
    setAllCandidatesBlocked(false)
    setSelectedModelName(null)
    setCeilingBanner(null)
    if (effectiveRootNeedId !== null) {
      loadSpecTree(effectiveRootNeedId)
        .then(() => setError(null))
        .catch(handleLoadSpecTreeError)
    }
    loadBlacklistCount(generationParent).catch(() => {
      void loadBlacklistCount(null)
    })
  }, [
    clearSpecTree,
    effectiveRootNeedId,
    handleLoadSpecTreeError,
    loadBlacklistCount,
    loadSpecTree,
    selectedParentKey,
  ])

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (generationParent === null || (!routerEnabled && modelId === null) || selectedLayerId === null) {
      return
    }
    const payload = {
      ...(routerEnabled ? {} : { model_id: modelId ?? undefined }),
      count,
      target_layer_id: selectedLayerId,
    }
    setIsGenerating(true)
    setAllCandidatesBlocked(false)
    try {
      const result =
        generationParent.kind === 'need'
          ? await generateSpecs(generationParent.id, payload)
          : await generateChildSpecs(generationParent.id, payload)
      setCandidates(result.candidates)
      setSelectedModelName(result.selected_model_name)
      setAllCandidatesBlocked(result.candidates.length === 0)
      setCeilingBanner(null)
      setError(null)
      onSuccessfulGeneration?.()
    } catch (generateError: unknown) {
      if (!handleCostCeilingError(generateError)) {
        setError(errorMessage(generateError))
      }
    } finally {
      setIsGenerating(false)
    }
  }

  async function handleAccept(candidate: GenerationCandidate) {
    if (generationParent === null || selectedLayerId === null) {
      return
    }
    const payload = { statement: candidate.statement, target_layer_id: selectedLayerId }
    try {
      const createdSpec =
        generationParent.kind === 'need'
          ? await createNeedSpec(generationParent.id, payload)
          : await createChildSpec(generationParent.id, payload)
      addClassifyingSpecId(createdSpec.id)
      setCandidates((currentCandidates) =>
        currentCandidates.filter((item) => item.index !== candidate.index),
      )
      if (effectiveRootNeedId !== null) {
        try {
          await loadSpecTree(effectiveRootNeedId)
          setError(null)
        } catch (loadError: unknown) {
          setError(errorMessage(loadError))
        }
      }
      try {
        const classification = await classifySpec(createdSpec.id)
        setSpecComplexity(createdSpec.id, classification.complexity)
      } catch (classifyError: unknown) {
        if (!handleCostCeilingError(classifyError)) {
          console.warn('Auto-classify failed after accepting spec', classifyError)
        }
      } finally {
        removeClassifyingSpecId(createdSpec.id)
      }
    } catch (acceptError: unknown) {
      setError(errorMessage(acceptError))
    }
  }

  async function handleReject(candidate: GenerationCandidate) {
    if (generationParent === null) {
      return
    }
    setCandidates((currentCandidates) =>
      currentCandidates.filter((item) => item.index !== candidate.index),
    )
    try {
      if (generationParent.kind === 'need') {
        await createNeedBlacklistEntry(generationParent.id, { statement: candidate.statement })
      } else {
        await createSpecBlacklistEntry(generationParent.id, { statement: candidate.statement })
      }
      await loadBlacklistCount(generationParent)
    } catch (rejectError: unknown) {
      console.warn('Blacklist reject failed', rejectError)
    }
  }

  return {
    allCandidatesBlocked,
    blacklistCount,
    candidates,
    classifyingSpecIds,
    count,
    handleAccept,
    handleGenerate,
    handleReject,
    isGenerating,
    selectedModelName,
    setCount,
  }
}
