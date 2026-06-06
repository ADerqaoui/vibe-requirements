import { useEffect, useState } from 'react'
import { fetchModels } from '../api/models'
import { fetchPromptContracts, previewPrompt, PromptTemplateInvalidApiError } from '../api/prompts'
import { useCostCeilingError, type CostCeilingBannerState } from '../hooks/useCostCeilingError'
import type { Model } from '../types/model'
import type { PromptPreviewResponse } from '../types/prompt'
import { CostCeilingBanner } from './CostCeilingBanner'

type PromptPreviewPanelProps = {
  task: string
  template: string
}

const EXAMPLES: Record<string, string> = {
  parent_statement: 'The system shall stop safely.',
  count: '3',
  spec_statement: 'The controller shall detect loss of signal within 100 ms.',
}

function exampleFor(variableName: string): string {
  return EXAMPLES[variableName] ?? 'Example value'
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function PromptPreviewPanel({ task, template }: PromptPreviewPanelProps) {
  const [requiredVariables, setRequiredVariables] = useState<string[]>([])
  const [variables, setVariables] = useState<Record<string, string>>({})
  const [models, setModels] = useState<Model[]>([])
  const [modelId, setModelId] = useState('')
  const [result, setResult] = useState<PromptPreviewResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [ceilingBanner, setCeilingBanner] = useState<CostCeilingBannerState>(null)
  const [isRunning, setIsRunning] = useState(false)
  const handleCostCeiling = useCostCeilingError({ setCeilingBanner, setError })

  useEffect(() => {
    let didCancel = false
    Promise.all([fetchPromptContracts(), fetchModels()])
      .then(([contracts, loadedModels]) => {
        if (didCancel) {
          return
        }
        const contractVariables = contracts[task] ?? []
        setRequiredVariables(contractVariables)
        setVariables(Object.fromEntries(contractVariables.map((name) => [name, exampleFor(name)])))
        setModels(loadedModels.filter((model) => model.enabled))
      })
      .catch((loadError: unknown) => {
        if (!didCancel) {
          setError(errorMessage(loadError))
        }
      })
    return () => {
      didCancel = true
    }
  }, [task])

  async function runPreview() {
    setIsRunning(true)
    setError(null)
    setCeilingBanner(null)
    setResult(null)
    try {
      const preview = await previewPrompt({
        task,
        template,
        variables,
        model_id: modelId === '' ? undefined : Number(modelId),
      })
      setResult(preview)
    } catch (previewError: unknown) {
      if (handleCostCeiling(previewError)) {
        return
      }
      if (previewError instanceof PromptTemplateInvalidApiError) {
        setError(previewError.reason)
        return
      }
      setError(errorMessage(previewError))
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <section className="rounded-md border border-neutral-200 bg-neutral-50 p-3">
      <div className="grid gap-2 md:grid-cols-2">
        {requiredVariables.map((variableName) => (
          <label key={variableName} className="grid gap-1 text-xs font-medium text-neutral-700">
            {variableName}
            <input
              className="rounded border border-neutral-300 px-2 py-1 text-sm font-normal"
              value={variables[variableName] ?? ''}
              onChange={(event) => setVariables({ ...variables, [variableName]: event.target.value })}
            />
          </label>
        ))}
        <label className="grid gap-1 text-xs font-medium text-neutral-700">
          Model
          <select
            className="rounded border border-neutral-300 px-2 py-1 text-sm font-normal"
            value={modelId}
            onChange={(event) => setModelId(event.target.value)}
          >
            <option value="">Default routed model</option>
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <button
        className="mt-3 rounded bg-neutral-800 px-3 py-1 text-sm text-white disabled:bg-neutral-400"
        disabled={isRunning}
        onClick={() => void runPreview()}
        type="button"
      >
        {isRunning ? 'Running...' : 'Run preview'}
      </button>
      {ceilingBanner && (
        <CostCeilingBanner
          spentSek={ceilingBanner.spentSek}
          ceilingSek={ceilingBanner.ceilingSek}
          currency={ceilingBanner.currency}
        />
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {result && (
        <div className="mt-3 grid gap-3">
          <p className="text-xs text-neutral-600">
            {result.model_name} - {result.cost_sek.toFixed(2)} SEK
          </p>
          <pre className="whitespace-pre-wrap rounded border border-neutral-200 bg-white p-2 text-xs">
            {result.rendered_prompt}
          </pre>
          <pre className="whitespace-pre-wrap rounded border border-neutral-200 bg-white p-2 text-xs">
            {result.output}
          </pre>
        </div>
      )}
    </section>
  )
}
