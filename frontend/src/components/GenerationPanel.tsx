import { FormEvent, useCallback, useEffect, useState } from 'react'
import { createNeedBlacklistEntry, createSpecBlacklistEntry } from '../api/blacklist'
import classifySpec from '../api/classification'
import { generateChildSpecs, generateSpecs } from '../api/generation'
import { createChildSpec, createNeedSpec } from '../api/specs'
import { useCostCeilingError, type CostCeilingBannerState } from '../hooks/useCostCeilingError'
import { useClassifyingSpecs } from '../hooks/useClassifyingSpecs'
import { useGenerationModels } from '../hooks/useGenerationModels'
import { useParentBlacklist } from '../hooks/useParentBlacklist'
import { useParentSpecTree } from '../hooks/useParentSpecTree'
import type { GenerationCandidate } from '../types/generation'
import { parentFromNeedId, parentKey, type GenerationParent } from '../types/generationParent'
import type { SpecTreeNode } from '../types/spec'
import { CostCeilingBanner } from './CostCeilingBanner'
import { GenerationCandidates } from './GenerationCandidates'
import { GenerationForm } from './GenerationForm'
import GenerationPanelHeader from './GenerationPanelHeader'
import { GenerationSpecSection } from './GenerationSpecSection'

type GenerationPanelProps = {
  rootNeedId?: number | null
  needId?: number | null
  parent?: GenerationParent | null
  onSelectSpec?: (spec: SpecTreeNode) => void
  onSuccessfulGeneration?: () => void
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function GenerationPanel({
  rootNeedId,
  needId,
  parent,
  onSelectSpec,
  onSuccessfulGeneration,
}: GenerationPanelProps) {
  const effectiveRootNeedId = rootNeedId ?? needId ?? null
  const generationParent = parent ?? parentFromNeedId(effectiveRootNeedId)
  const selectedParentKey = parentKey(generationParent)
  const [error, setError] = useState<string | null>(null)
  const [ceilingBanner, setCeilingBanner] = useState<CostCeilingBannerState>(null)
  const handleCostCeilingError = useCostCeilingError({ setCeilingBanner, setError })
  const handleError = useCallback((unknownError: unknown) => {
    setError(errorMessage(unknownError))
  }, [])
  const [count, setCount] = useState(5)
  const [candidates, setCandidates] = useState<GenerationCandidate[]>([])
  const [allCandidatesBlocked, setAllCandidatesBlocked] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const { modelId, models, setModelId } = useGenerationModels(handleError)
  const { blacklistCount, loadBlacklistCount } = useParentBlacklist()
  const { clearSpecTree, loadSpecTree, setSpecComplexity, specs } = useParentSpecTree()
  const { addClassifyingSpecId, classifyingSpecIds, removeClassifyingSpecId } = useClassifyingSpecs()

  useEffect(() => {
    clearSpecTree()
    setCandidates([])
    setAllCandidatesBlocked(false)
    setCeilingBanner(null)
    if (effectiveRootNeedId !== null) {
      loadSpecTree(effectiveRootNeedId)
        .then(() => setError(null))
        .catch(handleError)
    }
    loadBlacklistCount(generationParent).catch(() => {
      void loadBlacklistCount(null)
    })
  }, [clearSpecTree, effectiveRootNeedId, handleError, loadBlacklistCount, selectedParentKey])

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (generationParent === null || modelId === null) {
      return
    }
    setIsGenerating(true)
    setAllCandidatesBlocked(false)
    try {
      const result =
        generationParent.kind === 'need'
          ? await generateSpecs(generationParent.id, { model_id: modelId, count })
          : await generateChildSpecs(generationParent.id, { model_id: modelId, count })
      setCandidates(result.candidates)
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
    if (generationParent === null) {
      return
    }
    try {
      const createdSpec =
        generationParent.kind === 'need'
          ? await createNeedSpec(generationParent.id, { statement: candidate.statement })
          : await createChildSpec(generationParent.id, { statement: candidate.statement })
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

  if (generationParent === null) {
    return null
  }

  return (
    <section className="mt-6 border-t border-neutral-200 pt-5">
      <GenerationPanelHeader blacklistCount={blacklistCount} />
      {ceilingBanner && (
        <CostCeilingBanner
          ceilingSek={ceilingBanner.ceilingSek}
          currency={ceilingBanner.currency}
          spentSek={ceilingBanner.spentSek}
        />
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <GenerationForm
        count={count}
        isGenerating={isGenerating}
        modelId={modelId}
        models={models}
        onCountChange={setCount}
        onGenerate={handleGenerate}
        onModelIdChange={setModelId}
      />

      <GenerationCandidates candidates={candidates} onAccept={handleAccept} onReject={handleReject} />
      {allCandidatesBlocked && (
        <p className="mt-4 text-sm text-neutral-600">
          All candidates were blocked by the blacklist — try again or rephrase.
        </p>
      )}

      <GenerationSpecSection
        classifyingSpecIds={classifyingSpecIds}
        onSelectSpec={onSelectSpec}
        onSpecChanged={() => effectiveRootNeedId !== null && void loadSpecTree(effectiveRootNeedId)}
        selectedSpecId={parent?.kind === 'spec' ? parent.id : null}
        specs={specs}
      />
    </section>
  )
}
