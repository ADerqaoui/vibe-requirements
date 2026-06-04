import { useEffect, useState } from 'react'
import { createModel, deleteModel, fetchModels, updateModel } from '../api/models'
import { fetchSettings, updateSettings } from '../api/settings'
import type { Model, ModelPayload } from '../types/model'
import type { Setting, SettingsResponse } from '../types/setting'
import { CostPanel } from './CostPanel'
import { ModelTester } from './ModelTester'
import { PromptsPanel } from './PromptsPanel'
import { SettingsFields } from './SettingsFields'
import { SettingsModelCreateForm } from './SettingsModelCreateForm'
import { SettingsModelList } from './SettingsModelList'
import { SettingsProviderKeys } from './SettingsProviderKeys'
import { SettingsRouterToggle } from './SettingsRouterToggle'

const SETTING_KEYS = ['fx_rate_usd_sek', 'complexity_tier_map', 'router_default', 'cost_ceiling_sek']

function toErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return String(error)
}

function settingValue(settings: Setting[], key: string): string {
  return settings.find((setting) => setting.key === key)?.value ?? ''
}

type SettingsPanelProps = {
  costRefreshSignal?: number
}

export function SettingsPanel({ costRefreshSignal = 0 }: SettingsPanelProps) {
  const [models, setModels] = useState<Model[]>([])
  const [settingsResponse, setSettingsResponse] = useState<SettingsResponse>({
    settings: [],
    provider_keys: {},
    router_enabled: false,
  })
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

  async function handleCreateModel(payload: ModelPayload) {
    try {
      const model = await createModel(payload)
      setModels((currentModels) => [...currentModels, model])
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
        settingsResponse.router_enabled,
      )
      setSettingsResponse(response)
      setError(null)
    } catch (updateError: unknown) {
      setError(toErrorMessage(updateError))
    }
  }

  async function handleToggleRouter(enabled: boolean) {
    try {
      const response = await updateSettings(
        SETTING_KEYS.map((key) => ({ key, value: settingDrafts[key] ?? '' })),
        enabled,
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
          <SettingsModelCreateForm onCreateModel={handleCreateModel} />
          <SettingsModelList models={models} onDeleteModel={handleDeleteModel} onToggleModel={handleToggleModel} />
        </div>

        <div>
          <CostPanel refreshSignal={costRefreshSignal} />

          <h3 className="mt-5 text-sm font-semibold text-neutral-900">Settings</h3>
          <SettingsRouterToggle enabled={settingsResponse.router_enabled} onToggle={handleToggleRouter} />
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
