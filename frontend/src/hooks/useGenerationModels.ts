import { useEffect, useState } from 'react'
import { fetchModels } from '../api/models'
import type { Model } from '../types/model'

type UseGenerationModelsResult = {
  modelId: number | null
  models: Model[]
  setModelId: (modelId: number | null) => void
}

export function useGenerationModels(onError: (error: unknown) => void): UseGenerationModelsResult {
  const [models, setModels] = useState<Model[]>([])
  const [modelId, setModelId] = useState<number | null>(null)

  useEffect(() => {
    fetchModels()
      .then((loadedModels) => {
        const enabledModels = loadedModels.filter((model) => model.enabled)
        setModels(enabledModels)
        setModelId((currentModelId) => currentModelId ?? enabledModels[0]?.id ?? null)
      })
      .catch(onError)
  }, [onError])

  return { modelId, models, setModelId }
}
