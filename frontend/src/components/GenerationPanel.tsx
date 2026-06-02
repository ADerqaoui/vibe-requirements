import { FormEvent, useCallback, useEffect, useState } from 'react'
import {
  createNeedBlacklistEntry,
  createSpecBlacklistEntry,
} from '../api/blacklist'
import classifySpec from '../api/classification'
import { CostCeilingError, costCeilingMessage } from '../api/errors'
import { generateChildSpecs, generateSpecs } from '../api/generation'
import { createChildSpec, createNeedSpec } from '../api/specs'
import { useClassifyingSpecs } from '../hooks/useClassifyingSpecs'
import { useGenerationModels } from '../hooks/useGenerationModels'
import { useParentBlacklist } from '../hooks/useParentBlacklist'
import { useParentSpecTree } from '../hooks/useParentSpecTree'
import type { GenerationCandidate } from '../types/generation'
import type { SpecTreeNode } from '../types/spec'
import { GenerationCandidates } from './GenerationCandidates'
import { GenerationForm } from './GenerationForm'
import GenerationPanelHeader from './GenerationPanelHeader'
import { SpecList } from './SpecList'

export type GenerationParent = {
  kind: 'need' | 'spec'
  id: number
}

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

function parentFromNeedId(needId: number | null | undefined): GenerationParent | null {
  if (needId === null || needId === undefined) {
    return null
  }
  return { kind: 'need', id: needId }
}

function parentKey(parent: GenerationParent | null): string {
  return parent === null ? 'none' : `${parent.kind}:${parent.id}`
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
  const [ceilingBanner, setCeilingBanner] = useState<string | null>(null)
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
      if (generateError instanceof CostCeilingError) {
        setCeilingBanner(costCeilingMessage(generateError))
        setError(null)
      } else {
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
        if (classifyError instanceof CostCeilingError) {
          setCeilingBanner(costCeilingMessage(classifyError))
          setError(null)
        } else {
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
        <p className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {ceilingBanner}
        </p>
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

      <GenerationCandidates
        candidates={candidates}
        onAccept={handleAccept}
        onReject={handleReject}
      />
      {allCandidatesBlocked && (
        <p className="mt-4 text-sm text-neutral-600">
          All candidates were blocked by the blacklist — try again or rephrase.
        </p>
      )}

      <h3 className="mt-5 text-sm font-semibold text-neutral-900">Specs</h3>
      <SpecList
        classifyingSpecIds={classifyingSpecIds}
        onSelectSpec={onSelectSpec}
        onSpecChanged={() => {
          if (effectiveRootNeedId !== null) {
            void loadSpecTree(effectiveRootNeedId)
          }
        }}
        selectedSpecId={parent?.kind === 'spec' ? parent.id : null}
        specs={specs}
      />
    </section>
  )
}
