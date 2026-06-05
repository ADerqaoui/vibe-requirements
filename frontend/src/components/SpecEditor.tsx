import { useState } from 'react'

type SpecEditorProps = {
  initialText: string
  onCancel: () => void
  onSave: (text: string) => Promise<void>
}

export function SpecEditor({ initialText, onCancel, onSave }: SpecEditorProps) {
  const [draft, setDraft] = useState(initialText)
  const [isSaving, setIsSaving] = useState(false)
  const trimmedDraft = draft.trim()

  async function handleSave() {
    if (trimmedDraft === '') {
      return
    }
    setIsSaving(true)
    try {
      await onSave(trimmedDraft)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="grid flex-1 gap-2">
      <textarea
        aria-label="Spec text"
        className="min-h-24 rounded-md border border-neutral-300 px-3 py-2 text-sm font-normal text-neutral-900"
        onChange={(event) => setDraft(event.target.value)}
        value={draft}
      />
      <div className="flex gap-2">
        <button
          className="rounded bg-neutral-900 px-3 py-1.5 text-xs font-medium text-white disabled:bg-neutral-300"
          disabled={isSaving || trimmedDraft === ''}
          onClick={handleSave}
          type="button"
        >
          {isSaving ? 'Saving...' : 'Save'}
        </button>
        <button className="px-3 py-1.5 text-xs font-medium text-neutral-700" onClick={onCancel} type="button">
          Cancel
        </button>
      </div>
    </div>
  )
}
