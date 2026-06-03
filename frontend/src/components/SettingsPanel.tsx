import { FormEvent, useEffect, useState } from 'react'
import { createModel, deleteModel, fetchModels, updateModel } from '../api/models'
import { fetchSettings, updateSettings } from '../api/settings'
import type { Model, ModelPayload } from '../types/model'
import type { Setting, SettingsResponse } from '../types/setting'
import { CostPanel } from './CostPanel'
import { ModelTester } from './ModelTester'
import { PromptsPanel } from './PromptsPanel'
import { SettingsFields } from './SettingsFields'
import { SettingsModelList } from './SettingsModelList'
import { SettingsProviderKeys } from './SettingsProviderKeys'

const SETTING_KEYS = ['fx_rate_usd_sek', 'complexity_tier_map', 'router_default', 'cost_ceiling_sek']

type ModelDraft = {
  provider: string
  name: string
  identifier: string
  tier: string
}

const EMPTY_MODEL_DRAFT: ModelDraft = {
  provider: 'ollama',
  name: '',
  identifier: '',
  tier: 'mid',
}

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

function settingValue(settings: Setting[], key: string): string {
  return settings.find((setting) => setting.key === key)?.value ?? ''
}

function buildModelPayload(draft: ModelDraft): ModelPayload {
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

type SettingsPanelProps = {
  costRefreshSignal?: number
}

export function SettingsPanel({ costRefreshSignal = 0 }: SettingsPanelProps) {
  const [models, setModels] = useState<Model[]>([])
  const [settingsResponse, setSettingsResponse] = useState<SettingsResponse>({
    settings: [],
    provider_keys: {},
  })
  const [modelDraft, setModelDraft] = useState<ModelDraft>(EMPTY_MODEL_DRAFT)
  const [settingDrafts, setSettingDrafts] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([fetchModels(), fetchSettings()])
      .then(([loadedModels, loadedSettings]) => {
        setModels(loadedModels)
        setSettingsResponse(loadedSettings)
        setSettingDrafts(Object.fromEntries(SETTING_KEYS.map((key) => [key, settingValue(loadedSettings.settings, key)])))
        setError(null)
      })
      .catch((loadError: unknown) => setError(toErrorMessage(loadError)))
  }, [])

  async function handleCreateModel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (modelDraft.name.trim() === '') {
      return
    }
    try {
      const model = await createModel(buildModelPayload(modelDraft))
      setModels((currentModels) => [...currentModels, model])
      setModelDraft(EMPTY_MODEL_DRAFT)
      setError(null)
    } catch (createError: unknown) {
      setError(toErrorMessage(createError))
    }
  }

  async function handleToggleModel(model: Model) {
    try {
      const updatedModel = await updateModel(model.id, { enabled: !model.enabled })
      setModels((currentModels) =>
        currentModels.map((item) => (item.id === updatedModel.id ? updatedModel : item)),
      )
      setError(null)
    } catch (updateError: unknown) {
      setError(toErrorMessage(updateError))
    }
  }

  async function handleDeleteModel(model: Model) {
    try {
      await deleteModel(model.id)
      setModels((currentModels) => currentModels.filter((item) => item.id !== model.id))
      setError(null)
    } catch (deleteError: unknown) {
      setError(toErrorMessage(deleteError))
    }
  }

  async function handleSaveSettings() {
    try {
      const response = await updateSettings(
        SETTING_KEYS.map((key) => ({ key, value: settingDrafts[key] ?? '' })),
      )
      setSettingsResponse(response)
      setError(null)
    } catch (updateError: unknown) {
      setError(toErrorMessage(updateError))
    }
  }

  return (
    <section className="mt-8 max-w-5xl border-t border-neutral-200 pt-6">
      <h2 className="text-lg font-semibold text-neutral-950">Models and Settings</h2>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-neutral-900">Models</h3>
          <form className="mt-3 grid gap-2" onSubmit={handleCreateModel}>
            <select
              aria-label="Model provider"
              className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
              onChange={(event) => setModelDraft({ ...modelDraft, provider: event.target.value })}
              value={modelDraft.provider}
            >
              <option value="ollama">ollama</option>
              <option value="anthropic">anthropic</option>
              <option value="openai">openai</option>
              <option value="deepseek">deepseek</option>
            </select>
            <input
              aria-label="Model name"
              className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
              onChange={(event) => setModelDraft({ ...modelDraft, name: event.target.value })}
              placeholder="Name"
              value={modelDraft.name}
            />
            <input
              aria-label="Model identifier"
              className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
              onChange={(event) => setModelDraft({ ...modelDraft, identifier: event.target.value })}
              placeholder="Ollama tag or API model id"
              value={modelDraft.identifier}
            />
            <select
              aria-label="Model tier"
              className="rounded-md border border-neutral-300 px-3 py-2 text-sm"
              onChange={(event) => setModelDraft({ ...modelDraft, tier: event.target.value })}
              value={modelDraft.tier}
            >
              <option value="low">low</option>
              <option value="mid">mid</option>
              <option value="high">high</option>
            </select>
            <button className="w-fit rounded-md bg-neutral-950 px-3 py-2 text-sm text-white" type="submit">
              Add model
            </button>
          </form>

          <SettingsModelList models={models} onDeleteModel={handleDeleteModel} onToggleModel={handleToggleModel} />
        </div>

        <div>
          <CostPanel refreshSignal={costRefreshSignal} />

          <h3 className="mt-5 text-sm font-semibold text-neutral-900">Settings</h3>
          <SettingsFields
            onSaveSettings={handleSaveSettings}
            onSettingDraftsChange={setSettingDrafts}
            settingDrafts={settingDrafts}
            settingKeys={SETTING_KEYS}
          />

          <h3 className="mt-5 text-sm font-semibold text-neutral-900">Provider keys</h3>
          <SettingsProviderKeys providerKeys={settingsResponse.provider_keys} />
        </div>
      </div>
      <ModelTester models={models} />
      <PromptsPanel />
    </section>
  )
}
