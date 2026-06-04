import { FormEvent, useState } from 'react'
import type { ModelPayload } from '../types/model'

type ModelDraft = {
  provider: string
  name: string
  identifier: string
  tier: string
}

const EMPTY_DRAFT: ModelDraft = {
  provider: 'ollama',
  name: '',
  identifier: '',
  tier: 'mid',
}

type SettingsModelCreateFormProps = {
  onCreateModel: (payload: ModelPayload) => Promise<void>
}

function payloadFromDraft(draft: ModelDraft): ModelPayload {
  const identifier = draft.identifier.trim()
  return {
    provider: draft.provider,
    name: draft.name,
    tier: draft.tier,
    ollama_tag: draft.provider === 'ollama' ? identifier : undefined,
    api_model_id: draft.provider === 'ollama' ? undefined : identifier,
    enabled: draft.provider === 'ollama',
  }
}

export function SettingsModelCreateForm({ onCreateModel }: SettingsModelCreateFormProps) {
  const [draft, setDraft] = useState<ModelDraft>(EMPTY_DRAFT)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (draft.name.trim() === '') {
      return
    }
    await onCreateModel(payloadFromDraft(draft))
    setDraft(EMPTY_DRAFT)
  }

  return (
    <form className="mt-3 grid gap-2" onSubmit={handleSubmit}>
      <select
        aria-label="Model provider"
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
        onChange={(event) => setDraft({ ...draft, provider: event.target.value })}
        value={draft.provider}
      >
        <option value="ollama">ollama</option>
        <option value="anthropic">anthropic</option>
        <option value="openai">openai</option>
        <option value="deepseek">deepseek</option>
      </select>
      <input
        aria-label="Model name"
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
        onChange={(event) => setDraft({ ...draft, name: event.target.value })}
        placeholder="Name"
        value={draft.name}
      />
      <input
        aria-label="Model identifier"
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
        onChange={(event) => setDraft({ ...draft, identifier: event.target.value })}
        placeholder="Ollama tag or API model id"
        value={draft.identifier}
      />
      <select
        aria-label="Model tier"
        className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
        onChange={(event) => setDraft({ ...draft, tier: event.target.value })}
        value={draft.tier}
      >
        <option value="low">low</option>
        <option value="mid">mid</option>
        <option value="high">high</option>
      </select>
      <button className="w-fit rounded-md bg-neutral-950 px-3 py-2 text-sm text-white" type="submit">
        Add model
      </button>
    </form>
  )
}
