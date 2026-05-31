import { FormEvent, useEffect, useState } from 'react'
import { generateChildSpecs, generateSpecs } from '../api/generation'
import { fetchModels } from '../api/models'
import { createChildSpec, createNeedSpec, fetchNeedSpecTree } from '../api/specs'
import type { GenerationCandidate } from '../types/generation'
import type { Model } from '../types/model'
import type { SpecTreeNode } from '../types/spec'
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
      if (generationParent.kind === 'need') {
        await createNeedSpec(generationParent.id, { statement: candidate.statement })
      } else {
        await createChildSpec(generationParent.id, { statement: candidate.statement })
      }
      setCandidates((currentCandidates) =>
        currentCandidates.filter((item) => item.index !== candidate.index),
      )
      if (effectiveRootNeedId !== null) {
        await loadSpecTree(effectiveRootNeedId)
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
      <SpecList
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
