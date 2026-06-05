import { useCallback, useEffect, useState } from 'react'
import { classifySpec } from '../api/classification'
import { decideSpec, type SpecDecision } from '../api/decisions'
import { CostCeilingError, costCeilingMessage } from '../api/errors'
import { inspectSpec } from '../api/inspections'
import { fetchModels } from '../api/models'
import type { ClassificationVote } from '../types/classification'
import type { SpecInspection } from '../types/inspection'
import type { Model } from '../types/model'
import type { SpecTreeNode } from '../types/spec'
import { usePromptVariants } from '../hooks/usePromptVariants'
import { ModelChoice } from './ModelChoice'
import { PromptVariantSelect } from './PromptVariantSelect'
import { SpecNode } from './SpecNode'

type SpecListProps = {
  specs: SpecTreeNode[]
  classifyingSpecIds?: Set<number>
  onSelectSpec?: (spec: SpecTreeNode) => void
  onSpecChanged?: () => void
  routerEnabled?: boolean
  selectedSpecId?: number | null
}

function errorMessage(error: unknown): string {
  if (error instanceof CostCeilingError) {
    return costCeilingMessage(error)
  }
  return error instanceof Error ? error.message : String(error)
}

export function SpecList({
  specs,
  classifyingSpecIds = new Set(),
  onSelectSpec,
  onSpecChanged,
  routerEnabled = false,
  selectedSpecId,
}: SpecListProps) {
  const [complexityBySpec, setComplexityBySpec] = useState<Record<number, number>>({})
  const [inspectionBySpec, setInspectionBySpec] = useState<Record<number, SpecInspection>>({})
  const [loadingInspectionId, setLoadingInspectionId] = useState<number | null>(null)
  const [loadingSpecId, setLoadingSpecId] = useState<number | null>(null)
  const [modelId, setModelId] = useState<number | null>(null)
  const [models, setModels] = useState<Model[]>([])
  const [statusBySpec, setStatusBySpec] = useState<Record<number, string>>({})
  const [votesBySpec, setVotesBySpec] = useState<Record<number, ClassificationVote[]>>({})
  const [error, setError] = useState<string | null>(null)
  const handlePromptVariantError = useCallback((loadError: unknown) => {
    setError(errorMessage(loadError))
  }, [])
  const promptVariants = usePromptVariants('inspect_spec', null, handlePromptVariantError)

  useEffect(() => {
    fetchModels()
      .then((loadedModels) => {
        const enabledModels = loadedModels.filter((model) => model.enabled)
        setModels(enabledModels)
        setModelId((currentModelId) => currentModelId ?? enabledModels[0]?.id ?? null)
      })
      .catch((loadError: unknown) => setError(errorMessage(loadError)))
  }, [])

  async function handleClassify(spec: SpecTreeNode) {
    setLoadingSpecId(spec.id)
    try {
      const result = await classifySpec(spec.id)
      setComplexityBySpec((currentValues) => ({ ...currentValues, [spec.id]: result.complexity }))
      setVotesBySpec((currentValues) => ({ ...currentValues, [spec.id]: result.votes }))
      setError(null)
    } catch (classifyError: unknown) {
      setError(errorMessage(classifyError))
    } finally {
      setLoadingSpecId(null)
    }
  }

  async function handleInspect(spec: SpecTreeNode) {
    if (!routerEnabled && modelId === null) {
      setError('Select an inspection model first')
      return
    }
    setLoadingInspectionId(spec.id)
    try {
      const inspection = await inspectSpec(
        spec.id,
        routerEnabled ? undefined : modelId ?? undefined,
        routerEnabled ? undefined : promptVariants.promptId ?? undefined,
      )
      setInspectionBySpec((currentValues) => ({ ...currentValues, [spec.id]: inspection }))
      setError(null)
    } catch (inspectError: unknown) {
      setError(errorMessage(inspectError))
    } finally {
      setLoadingInspectionId(null)
    }
  }

  async function handleDecision(spec: SpecTreeNode, decision: SpecDecision) {
    try {
      const updatedSpec = await decideSpec(spec.id, decision)
      setStatusBySpec((currentValues) => ({ ...currentValues, [spec.id]: updatedSpec.status }))
      onSpecChanged?.()
      setError(null)
    } catch (decisionError: unknown) {
      setError(errorMessage(decisionError))
    }
  }

  if (specs.length === 0) {
    return <p className="mt-2 text-sm text-neutral-500">No specs accepted yet.</p>
  }

  return (
    <>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <div className="mt-2 max-w-xs">
        <ModelChoice
          ariaLabel="Inspection model"
          label="Inspection model"
          modelId={modelId}
          models={models}
          onModelIdChange={setModelId}
          routerEnabled={routerEnabled}
        />
      </div>
      <div className="mt-2 max-w-xs">
        <PromptVariantSelect
          ariaLabel="Inspection prompt"
          label="Inspection prompt"
          onPromptIdChange={promptVariants.setPromptId}
          promptId={promptVariants.promptId}
          routerEnabled={routerEnabled}
          variants={promptVariants.variants}
        />
      </div>
      <ul className="mt-2 space-y-2">
        {specs.map((spec) => (
          <SpecNode
            classifyingSpecIds={classifyingSpecIds}
            complexityBySpec={complexityBySpec}
            inspectionBySpec={inspectionBySpec}
            key={spec.id}
            loadingInspectionId={loadingInspectionId}
            loadingSpecId={loadingSpecId}
            onClassify={handleClassify}
            onDecide={handleDecision}
            onInspect={handleInspect}
            onSelectSpec={onSelectSpec}
            onSpecChanged={onSpecChanged}
            selectedSpecId={selectedSpecId}
            spec={spec}
            statusBySpec={statusBySpec}
            votesBySpec={votesBySpec}
          />
        ))}
      </ul>
    </>
  )
}
