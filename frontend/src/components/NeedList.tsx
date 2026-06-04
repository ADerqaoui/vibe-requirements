import { FormEvent, useEffect, useState } from 'react'
import { createNeed, deleteNeed, fetchProjectNeeds, updateNeed } from '../api/needs'
import type { GenerationParent } from '../types/generationParent'
import type { Need, NeedPayload } from '../types/need'
import type { SpecTreeNode } from '../types/spec'
import { GenerationPanel } from './GenerationPanel'
import { NeedCreateForm, type NeedDraft } from './NeedCreateForm'
import { NeedRow } from './NeedRow'

type NeedListProps = {
  onSuccessfulGeneration?: () => void
  projectId: number | null
  routerEnabled?: boolean
}

const EMPTY_DRAFT: NeedDraft = {
  statement: '',
  context: '',
  constraints: '',
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

function draftFromNeed(need: Need): NeedDraft {
  return {
    statement: need.statement,
    context: need.context ?? '',
    constraints: need.constraints ?? '',
  }
}

function payloadFromDraft(draft: NeedDraft): NeedPayload {
  return {
    statement: draft.statement,
    context: draft.context,
    constraints: draft.constraints,
  }
}

export function NeedList({ onSuccessfulGeneration, projectId, routerEnabled = false }: NeedListProps) {
  const [needs, setNeeds] = useState<Need[]>([])
  const [selectedNeedId, setSelectedNeedId] = useState<number | null>(null)
  const [selectedParent, setSelectedParent] = useState<GenerationParent | null>(null)
  const [draft, setDraft] = useState<NeedDraft>(EMPTY_DRAFT)
  const [editingNeedId, setEditingNeedId] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState<NeedDraft>(EMPTY_DRAFT)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (projectId === null) {
      setNeeds([])
      setSelectedNeedId(null)
      setSelectedParent(null)
      return
    }

    let didCancel = false
    setIsLoading(true)
    fetchProjectNeeds(projectId)
      .then((loadedNeeds) => {
        if (didCancel) {
          return
        }
        setNeeds(loadedNeeds)
        const nextNeedId = loadedNeeds[0]?.id ?? null
        setSelectedNeedId(nextNeedId)
        setSelectedParent(nextNeedId === null ? null : { kind: 'need', id: nextNeedId })
        setError(null)
      })
      .catch((loadError: unknown) => {
        if (!didCancel) {
          setError(toErrorMessage(loadError))
        }
      })
      .finally(() => {
        if (!didCancel) {
          setIsLoading(false)
        }
      })

    return () => {
      didCancel = true
    }
  }, [projectId])

  async function handleCreateNeed(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (projectId === null || draft.statement.trim().length === 0) {
      return
    }
    try {
      const need = await createNeed(projectId, payloadFromDraft(draft))
      setNeeds((currentNeeds) => [...currentNeeds, need])
      setSelectedNeedId(need.id)
      setSelectedParent({ kind: 'need', id: need.id })
      setDraft(EMPTY_DRAFT)
      setError(null)
    } catch (createError: unknown) {
      setError(toErrorMessage(createError))
    }
  }

  async function handleUpdateNeed(needId: number) {
    if (editDraft.statement.trim().length === 0) {
      return
    }
    try {
      const need = await updateNeed(needId, payloadFromDraft(editDraft))
      setNeeds((currentNeeds) => currentNeeds.map((item) => (item.id === need.id ? need : item)))
      setEditingNeedId(null)
      setEditDraft(EMPTY_DRAFT)
      setError(null)
    } catch (updateError: unknown) {
      setError(toErrorMessage(updateError))
    }
  }

  async function handleDeleteNeed(need: Need) {
    if (!window.confirm(`Delete need "${need.statement}"?`)) {
      return
    }
    try {
      await deleteNeed(need.id)
      setNeeds((currentNeeds) => currentNeeds.filter((item) => item.id !== need.id))
      if (selectedNeedId === need.id) {
        setSelectedNeedId(null)
        setSelectedParent(null)
      }
      setError(null)
    } catch (deleteError: unknown) {
      setError(toErrorMessage(deleteError))
    }
  }

  function beginEdit(need: Need) {
    setEditingNeedId(need.id)
    setEditDraft(draftFromNeed(need))
  }

  function selectNeed(needId: number) {
    setSelectedNeedId(needId)
    setSelectedParent({ kind: 'need', id: needId })
  }

  function selectSpec(spec: SpecTreeNode) {
    setSelectedParent({ kind: 'spec', id: spec.id, layer_id: spec.layer_id })
  }

  if (projectId === null) {
    return <div className="text-sm text-neutral-500">Select a project to manage needs.</div>
  }

  return (
    <section className="max-w-3xl">
      <h2 className="text-lg font-semibold text-neutral-950">Needs</h2>

      <NeedCreateForm draft={draft} onDraftChange={setDraft} onSubmit={handleCreateNeed} />

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {isLoading && <p className="mt-6 text-sm text-neutral-500">Loading needs...</p>}
      {!isLoading && needs.length === 0 && (
        <p className="mt-6 text-sm text-neutral-500">No needs yet.</p>
      )}

      <ul className="mt-4 space-y-2">
        {needs.map((need) => (
          <NeedRow
            editDraft={editDraft}
            isEditing={editingNeedId === need.id}
            isSelected={selectedParent?.kind === 'need' && selectedParent.id === need.id}
            key={need.id}
            need={need}
            onBeginEdit={beginEdit}
            onDelete={handleDeleteNeed}
            onEditDraftChange={setEditDraft}
            onSave={handleUpdateNeed}
            onSelect={selectNeed}
          />
        ))}
      </ul>
      <GenerationPanel
        onSuccessfulGeneration={onSuccessfulGeneration}
        onSelectSpec={selectSpec}
        parent={selectedParent}
        rootNeedId={selectedNeedId}
        routerEnabled={routerEnabled}
      />
    </section>
  )
}
