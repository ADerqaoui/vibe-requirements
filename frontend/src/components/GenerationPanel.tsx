import { useCallback, useState } from 'react'
import { useAllowedChildLayers } from '../hooks/useAllowedChildLayers'
import type { CostCeilingBannerState } from '../hooks/useCostCeilingError'
import { useGenerationActions } from '../hooks/useGenerationActions'
import { useGenerationModels } from '../hooks/useGenerationModels'
import { useParentSpecTree } from '../hooks/useParentSpecTree'
import { usePromptVariants } from '../hooks/usePromptVariants'
import { parentFromNeedId, type GenerationParent } from '../types/generationParent'
import type { SpecTreeNode } from '../types/spec'
import { errorMessage } from '../utils/errorMessage'
import { CostCeilingBanner } from './CostCeilingBanner'
import { GenerationCandidates } from './GenerationCandidates'
import { GenerationForm } from './GenerationForm'
import GenerationPanelHeader from './GenerationPanelHeader'
import { GenerationSpecSection } from './GenerationSpecSection'
import { ManualSpecForm } from './ManualSpecForm'

type GenerationPanelProps = {
  rootNeedId?: number | null
  needId?: number | null
  parent?: GenerationParent | null
  onSelectSpec?: (spec: SpecTreeNode) => void
  onSuccessfulGeneration?: () => void
  routerEnabled?: boolean
}

export function GenerationPanel({
  rootNeedId,
  needId,
  parent,
  onSelectSpec,
  onSuccessfulGeneration,
  routerEnabled = false,
}: GenerationPanelProps) {
  const effectiveRootNeedId = rootNeedId ?? needId ?? null
  const generationParent = parent ?? parentFromNeedId(effectiveRootNeedId)
  const [error, setError] = useState<string | null>(null)
  const [ceilingBanner, setCeilingBanner] = useState<CostCeilingBannerState>(null)
  const [isAddingManualSpec, setIsAddingManualSpec] = useState(false)
  const handleError = useCallback((unknownError: unknown) => {
    setError(errorMessage(unknownError))
  }, [])
  const { allowedLayers, selectedLayerId, setSelectedLayerId } = useAllowedChildLayers(generationParent, handleError)
  const { modelId, models, setModelId } = useGenerationModels(handleError)
  const promptVariants = usePromptVariants(
    generationParent?.kind === 'need' ? 'generate_need_to_spec' : 'generate_spec_to_child',
    selectedLayerId,
    handleError,
    selectedLayerId !== null,
  )
  const { clearSpecTree, loadSpecTree, setSpecComplexity, specs } = useParentSpecTree()
  const {
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
    selectedPromptName,
    setCount,
  } = useGenerationActions({
    clearSpecTree,
    effectiveRootNeedId,
    generationParent,
    loadSpecTree,
    modelId,
    onSuccessfulGeneration,
    promptId: promptVariants.promptId,
    routerEnabled,
    selectedLayerId,
    setCeilingBanner,
    setError,
    setSpecComplexity,
  })

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
      {generationParent.kind === 'need' && (
        <div className="mt-3">
          <button
            className="rounded border border-neutral-300 px-3 py-1.5 text-xs font-medium text-neutral-900"
            onClick={() => setIsAddingManualSpec(true)}
            type="button"
          >
            Add requirement
          </button>
          {isAddingManualSpec && (
            <ManualSpecForm
              onCancel={() => setIsAddingManualSpec(false)}
              onCreated={() => {
                setIsAddingManualSpec(false)
                if (effectiveRootNeedId !== null) {
                  void loadSpecTree(effectiveRootNeedId)
                }
              }}
              parent={generationParent}
            />
          )}
        </div>
      )}
      <GenerationForm
        allowedLayers={allowedLayers}
        count={count}
        isGenerating={isGenerating}
        modelId={modelId}
        models={models}
        onCountChange={setCount}
        onGenerate={handleGenerate}
        onLayerChange={setSelectedLayerId}
        onModelIdChange={setModelId}
        onPromptIdChange={promptVariants.setPromptId}
        promptId={promptVariants.promptId}
        promptVariants={promptVariants.variants}
        routerEnabled={routerEnabled}
        selectedLayerId={selectedLayerId}
      />
      {selectedModelName && <p className="mt-2 text-sm text-neutral-600">Generated with: {selectedModelName}</p>}
      {selectedPromptName && <p className="mt-1 text-sm text-neutral-600">Prompt: {selectedPromptName}</p>}

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
        routerEnabled={routerEnabled}
        selectedSpecId={parent?.kind === 'spec' ? parent.id : null}
        specs={specs}
      />
    </section>
  )
}
