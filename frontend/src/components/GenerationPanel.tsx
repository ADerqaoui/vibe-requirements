import { FormEvent, useEffect, useState } from 'react'
import { generateSpecs } from '../api/generation'
import { fetchModels } from '../api/models'
import { createNeedSpec, fetchNeedSpecs } from '../api/specs'
import type { GenerationCandidate } from '../types/generation'
import type { Model } from '../types/model'
import type { Spec } from '../types/spec'
import { SpecList } from './SpecList'

type GenerationPanelProps = {
  needId: number | null
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

export function GenerationPanel({ needId }: GenerationPanelProps) {
  const [models, setModels] = useState<Model[]>([])
  const [modelId, setModelId] = useState<number | null>(null)
  const [count, setCount] = useState(5)
  const [candidates, setCandidates] = useState<GenerationCandidate[]>([])
  const [specs, setSpecs] = useState<Spec[]>([])
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

  useEffect(() => {
    if (needId === null) {
      setCandidates([])
      setSpecs([])
      return
    }
    fetchNeedSpecs(needId)
      .then((loadedSpecs) => {
        setSpecs(loadedSpecs)
        setError(null)
      })
      .catch((loadError: unknown) => setError(errorMessage(loadError)))
  }, [needId])

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (needId === null || modelId === null) {
      return
    }
    setIsGenerating(true)
    try {
      const result = await generateSpecs(needId, { model_id: modelId, count })
      setCandidates(result.candidates)
      setError(null)
    } catch (generateError: unknown) {
      setError(errorMessage(generateError))
    } finally {
      setIsGenerating(false)
    }
  }

  async function handleAccept(candidate: GenerationCandidate) {
    if (needId === null) {
      return
    }
    try {
      await createNeedSpec(needId, { statement: candidate.statement })
      setCandidates((currentCandidates) =>
        currentCandidates.filter((item) => item.index !== candidate.index),
      )
      const loadedSpecs = await fetchNeedSpecs(needId)
      setSpecs(loadedSpecs)
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

  if (needId === null) {
    return null
  }

  return (
    <section className="mt-6 border-t border-neutral-200 pt-5">
      <h3 className="text-sm font-semibold text-neutral-900">Generate specs</h3>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <form className="mt-3 flex flex-wrap items-end gap-3" onSubmit={handleGenerate}>
        <label className="grid gap-1 text-xs font-medium text-neutral-600">
          Model
          <select
            aria-label="Generation model"
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
        <label className="grid gap-1 text-xs font-medium text-neutral-600">
          Count
          <input
            aria-label="Generation count"
            className="w-24 rounded-md border border-neutral-300 px-3 py-2 text-sm font-normal text-neutral-900"
            max={10}
            min={1}
            onChange={(event) => setCount(Number(event.target.value))}
            type="number"
            value={count}
          />
        </label>
        <button
          className="rounded-md bg-neutral-950 px-3 py-2 text-sm text-white disabled:bg-neutral-400"
          disabled={isGenerating || modelId === null}
          type="submit"
        >
          {isGenerating ? 'Generating...' : 'Generate'}
        </button>
      </form>

      <ul className="mt-4 space-y-2">
        {candidates.map((candidate) => (
          <li className="rounded-md border border-neutral-200 bg-white p-3" key={candidate.index}>
            <p className="text-sm text-neutral-950">{candidate.statement}</p>
            <div className="mt-2 flex gap-3">
              <button className="text-xs font-medium text-neutral-900" onClick={() => handleAccept(candidate)} type="button">
                Accept
              </button>
              <button className="text-xs text-red-600" onClick={() => handleReject(candidate)} type="button">
                Reject
              </button>
            </div>
          </li>
        ))}
      </ul>

      <h3 className="mt-5 text-sm font-semibold text-neutral-900">Specs</h3>
      <SpecList specs={specs} />
    </section>
  )
}
