import { useEffect, useState } from 'react'
import { fetchPromptVariants } from '../api/prompts'
import type { PromptVariant } from '../types/prompt'

type UsePromptVariantsResult = {
  promptId: number | null
  variants: PromptVariant[]
  setPromptId: (promptId: number | null) => void
}

export function usePromptVariants(
  task: string,
  layerId: number | null,
  onError: (error: unknown) => void,
  enabled = true,
): UsePromptVariantsResult {
  const [variants, setVariants] = useState<PromptVariant[]>([])
  const [promptId, setPromptId] = useState<number | null>(null)

  useEffect(() => {
    if (!enabled) {
      setVariants([])
      setPromptId(null)
      return
    }
    fetchPromptVariants(task, layerId)
      .then((loadedVariants) => {
        const defaultVariant = loadedVariants.find((variant) => variant.is_default) ?? loadedVariants[0]
        setVariants(loadedVariants)
        setPromptId((currentPromptId) => {
          const stillExists = loadedVariants.some((variant) => variant.prompt_id === currentPromptId)
          return stillExists ? currentPromptId : defaultVariant?.prompt_id ?? null
        })
      })
      .catch(onError)
  }, [task, layerId, onError, enabled])

  return { promptId, variants, setPromptId }
}
