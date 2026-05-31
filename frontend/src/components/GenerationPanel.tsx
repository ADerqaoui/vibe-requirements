import { FormEvent, useEffect, useState } from 'react'
import {
  createNeedBlacklistEntry,
  createSpecBlacklistEntry,
  fetchNeedBlacklist,
  fetchSpecBlacklist,
} from '../api/blacklist'
import { generateChildSpecs, generateSpecs } from '../api/generation'
import { fetchModels } from '../api/models'
import { createChildSpec, createNeedSpec, fetchNeedSpecTree } from '../api/specs'
import type { GenerationCandidate } from '../types/generation'
import type { Model } from '../types/model'
import type { SpecTreeNode } from '../types/spec'
import { GenerationCandidates } from './GenerationCandidates'
import { GenerationForm } from './GenerationForm'
import { GenerationPanelHeader } from './GenerationPanelHeader'
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
  const [blacklistCount, setBlacklistCount] = useState(0)
  const [allCandidatesBlocked, setAllCandidatesBlocked] = useState(false)
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

  async function loadBlacklistCount(parentToLoad: GenerationParent | null) {
    if (parentToLoad === null) {
      setBlacklistCount(0)
      return
    }
    const entries =
      parentToLoad.kind === 'need'
        ? await fetchNeedBlacklist(parentToLoad.id)
        : await fetchSpecBlacklist(parentToLoad.id)
    setBlacklistCount(entries.length)
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
    setAllCandidatesBlocked(false)
    loadBlacklistCount(generationParent).catch(() => {
      setBlacklistCount(0)
    })
  }, [parentKey(generationParent)])

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
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      <GenerationForm count={count} isGenerating={isGenerating} modelId={modelId} models={models} onCountChange={setCount} onGenerate={handleGenerate} onModelIdChange={setModelId} />

      <GenerationCandidates candidates={candidates} onAccept={handleAccept} onReject={handleReject} />
      {allCandidatesBlocked && (
        <p className="mt-4 text-sm text-neutral-600">
          All candidates were blocked by the blacklist — try again or rephrase.
        </p>
      )}

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
