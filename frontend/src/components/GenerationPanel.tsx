import { FormEvent, useEffect, useState } from 'react'
import { classifySpec } from '../api/classification'
import { generateChildSpecs, generateSpecs } from '../api/generation'
import { fetchModels } from '../api/models'
import { createChildSpec, createNeedSpec, fetchNeedSpecTree } from '../api/specs'
import type { GenerationCandidate } from '../types/generation'
import type { Model } from '../types/model'
import type { SpecTreeNode } from '../types/spec'
import { GenerationCandidates } from './GenerationCandidates'
import { GenerationForm } from './GenerationForm'
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

export function GenerationPanel({ rootNeedId, needId, parent, onSelectSpec }: GenerationPanelProps) {
  const effectiveRootNeedId = rootNeedId ?? needId ?? null
  const generationParent = parent ?? parentFromNeedId(effectiveRootNeedId)
  const [models, setModels] = useState<Model[]>([])
  const [modelId, setModelId] = useState<number | null>(null)
  const [count, setCount] = useState(5)
  const [candidates, setCandidates] = useState<GenerationCandidate[]>([])
  const [classifyingSpecIds, setClassifyingSpecIds] = useState<Set<number>>(new Set())
  const [specs, setSpecs] = useState<SpecTreeNode[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  useEffect(() => {
    fetchModels()
      .then((loadedModels) => {
        const enabledModels = loadedModels.filter((model) => model.enabled)
        setModels(enabledModels)
        setModelId((currentModelId) => currentModelId ?? enabledModels[0]?.id ?? null)
      })
      .catch((loadError: unknown) => setError(errorMessage(loadError)))
  }, [])

  async function loadSpecTree(needId: number) {
    const loadedSpecs = await fetchNeedSpecTree(needId)
    setSpecs(loadedSpecs)
    setError(null)
  }

  useEffect(() => {
    setSpecs([])
    if (effectiveRootNeedId === null) {
      return
    }
    loadSpecTree(effectiveRootNeedId)
      .catch((loadError: unknown) => setError(errorMessage(loadError)))
  }, [effectiveRootNeedId])

  useEffect(() => {
    setCandidates([])
  }, [parentKey(generationParent)])

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (generationParent === null || modelId === null) {
      return
    }
    setIsGenerating(true)
    try {
      const result =
        generationParent.kind === 'need'
          ? await generateSpecs(generationParent.id, { model_id: modelId, count })
          : await generateChildSpecs(generationParent.id, { model_id: modelId, count })
      setCandidates(result.candidates)
      setError(null)
    } catch (generateError: unknown) {
      setError(errorMessage(generateError))
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
      setClassifyingSpecIds((currentIds) => new Set(currentIds).add(createdSpec.id))
      setCandidates((currentCandidates) =>
        currentCandidates.filter((item) => item.index !== candidate.index),
      )
      if (effectiveRootNeedId !== null) {
        await loadSpecTree(effectiveRootNeedId)
      }
      try {
        const classification = await classifySpec(createdSpec.id)
        setSpecs((currentSpecs) =>
          updateSpecComplexity(currentSpecs, createdSpec.id, classification.complexity),
        )
      } catch (classifyError: unknown) {
        console.warn('Auto-classify failed after accepting spec', classifyError)
      } finally {
        setClassifyingSpecIds((currentIds) => {
          const nextIds = new Set(currentIds)
          nextIds.delete(createdSpec.id)
          return nextIds
        })
      }
      setError(null)
    } catch (acceptError: unknown) {
      setError(errorMessage(acceptError))
    }
  }

  function handleReject(candidate: GenerationCandidate) {
    setCandidates((currentCandidates) =>
      currentCandidates.filter((item) => item.index !== candidate.index),
    )
  }

  if (generationParent === null) {
    return null
  }

  return (
    <section className="mt-6 border-t border-neutral-200 pt-5">
      <h3 className="text-sm font-semibold text-neutral-900">Generate specs</h3>
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

      <h3 className="mt-5 text-sm font-semibold text-neutral-900">Specs</h3>
      <SpecList
        autoClassifyingSpecIds={classifyingSpecIds}
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
