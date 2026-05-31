import { FormEvent, useEffect, useState } from 'react'
import { createNeed, deleteNeed, fetchProjectNeeds, updateNeed } from '../api/needs'
import type { Need, NeedPayload } from '../types/need'
import type { Spec } from '../types/spec'
import { GenerationPanel, type GenerationParent } from './GenerationPanel'

type NeedListProps = {
  projectId: number | null
}

type NeedDraft = {
  statement: string
  context: string
  constraints: string
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

export function NeedList({ projectId }: NeedListProps) {
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

  function selectSpec(spec: Spec) {
    setSelectedParent({ kind: 'spec', id: spec.id })
  }

  if (projectId === null) {
    return <div className="text-sm text-neutral-500">Select a project to manage needs.</div>
  }

  return (
    <section className="max-w-3xl">
      <h2 className="text-lg font-semibold text-neutral-950">Needs</h2>

      <form className="mt-4 grid gap-2" onSubmit={handleCreateNeed}>
        <input
          aria-label="Need statement"
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
          onChange={(event) => setDraft({ ...draft, statement: event.target.value })}
          placeholder="Statement"
          value={draft.statement}
        />
        <input
          aria-label="Need context"
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
          onChange={(event) => setDraft({ ...draft, context: event.target.value })}
          placeholder="Context"
          value={draft.context}
        />
        <input
          aria-label="Need constraints"
          className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
          onChange={(event) => setDraft({ ...draft, constraints: event.target.value })}
          placeholder="Constraints"
          value={draft.constraints}
        />
        <button className="w-fit rounded-md bg-neutral-950 px-3 py-2 text-sm text-white" type="submit">
          Add need
        </button>
      </form>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {isLoading && <p className="mt-6 text-sm text-neutral-500">Loading needs...</p>}
      {!isLoading && needs.length === 0 && (
        <p className="mt-6 text-sm text-neutral-500">No needs yet.</p>
      )}

      <ul className="mt-4 space-y-2">
        {needs.map((need) => {
          const isSelected = selectedNeedId === need.id
          const isEditing = editingNeedId === need.id
          return (
            <li
              className={`rounded-md border bg-white p-3 ${
                isSelected ? 'border-neutral-950' : 'border-neutral-200'
              }`}
              key={need.id}
            >
              {isEditing ? (
                <div className="grid gap-2">
                  <input
                    aria-label={`Edit statement ${need.id}`}
                    className="rounded-md border border-neutral-300 px-2 py-1 text-sm"
                    onChange={(event) => setEditDraft({ ...editDraft, statement: event.target.value })}
                    value={editDraft.statement}
                  />
                  <input
                    aria-label={`Edit context ${need.id}`}
                    className="rounded-md border border-neutral-300 px-2 py-1 text-sm"
                    onChange={(event) => setEditDraft({ ...editDraft, context: event.target.value })}
                    value={editDraft.context}
                  />
                  <input
                    aria-label={`Edit constraints ${need.id}`}
                    className="rounded-md border border-neutral-300 px-2 py-1 text-sm"
                    onChange={(event) =>
                      setEditDraft({ ...editDraft, constraints: event.target.value })
                    }
                    value={editDraft.constraints}
                  />
                  <button
                    className="w-fit text-sm font-medium text-neutral-900"
                    onClick={() => handleUpdateNeed(need.id)}
                    type="button"
                  >
                    Save
                  </button>
                </div>
              ) : (
                <div className="flex items-start justify-between gap-3">
                  <button
                    className="min-w-0 flex-1 text-left"
                    onClick={() => selectNeed(need.id)}
                    type="button"
                  >
                    <span className="block text-sm font-medium text-neutral-950">{need.statement}</span>
                    {need.context && <span className="block text-xs text-neutral-500">{need.context}</span>}
                    {need.constraints && (
                      <span className="block text-xs text-neutral-500">{need.constraints}</span>
                    )}
                    {need.complexity === null && (
                      <span className="mt-2 inline-block rounded bg-amber-100 px-2 py-1 text-xs text-amber-800">
                        Unclassified
                      </span>
                    )}
                  </button>
                  <button className="text-xs text-neutral-500" onClick={() => beginEdit(need)} type="button">
                    Edit
                  </button>
                  <button className="text-xs text-red-600" onClick={() => handleDeleteNeed(need)} type="button">
                    Delete
                  </button>
                </div>
              )}
            </li>
          )
        })}
      </ul>
      <GenerationPanel onSelectSpec={selectSpec} parent={selectedParent} />
    </section>
  )
}
