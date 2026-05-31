import { useEffect, useState } from 'react'
import { classifySpec } from '../api/classification'
import { decideSpec, type SpecDecision } from '../api/decisions'
import { inspectSpec } from '../api/inspections'
import { fetchModels } from '../api/models'
import type { ClassificationVote } from '../types/classification'
import type { SpecInspection } from '../types/inspection'
import type { Model } from '../types/model'
import type { SpecTreeNode } from '../types/spec'
import { SpecNode } from './SpecNode'

type SpecListProps = {
  specs: SpecTreeNode[]
  autoClassifyingSpecIds?: Set<number>
  onSelectSpec?: (spec: SpecTreeNode) => void
  onSpecChanged?: () => void
  selectedSpecId?: number | null
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

export function SpecList({
  specs,
  autoClassifyingSpecIds = new Set(),
  onSelectSpec,
  onSpecChanged,
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
    if (modelId === null) {
      setError('Select an inspection model first')
      return
    }
    setLoadingInspectionId(spec.id)
    try {
      const inspection = await inspectSpec(spec.id, modelId)
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
      <label className="mt-2 grid max-w-xs gap-1 text-xs font-medium text-neutral-600">
        Inspection model
        <select
          aria-label="Inspection model"
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm font-normal text-neutral-900"
          disabled={models.length === 0}
          onChange={(event) => setModelId(Number(event.target.value))}
          value={modelId ?? ''}
        >
          {models.length === 0 && <option value="">No enabled models</option>}
          {models.map((model) => (
            <option key={model.id} value={model.id}>
              {model.name}
            </option>
          ))}
        </select>
      </label>
      <ul className="mt-2 space-y-2">
        {specs.map((spec) => (
          <SpecNode
            autoClassifyingSpecIds={autoClassifyingSpecIds}
            complexityBySpec={complexityBySpec}
            inspectionBySpec={inspectionBySpec}
            key={spec.id}
            loadingInspectionId={loadingInspectionId}
            loadingSpecId={loadingSpecId}
            onClassify={handleClassify}
            onDecide={handleDecision}
            onInspect={handleInspect}
            onSelectSpec={onSelectSpec}
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
