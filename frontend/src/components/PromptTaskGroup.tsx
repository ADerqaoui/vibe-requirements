import type { Layer } from '../types/layer'
import type { Prompt } from '../types/prompt'
import { PromptEditor } from './PromptEditor'
import { PromptHistory } from './PromptHistory'

type PromptTaskGroupProps = {
  task: string
  prompts: Prompt[]
  layers: Layer[]
  editingKey: string | null
  historyKey: string | null
  onEdit: (key: string) => void
  onHistory: (key: string) => void
  onCancelEdit: () => void
  onCloseHistory: () => void
  onChanged: () => void
}

function slotKey(prompt: Prompt): string {
  return `${prompt.task}:${prompt.layer_id ?? 'global'}`
}

function scopeLabel(prompt: Prompt): string {
  return prompt.layer_id === null ? 'Global' : prompt.layer_name ?? `Layer ${prompt.layer_id}`
}

export function PromptTaskGroup({
  task,
  prompts,
  layers,
  editingKey,
  historyKey,
  onEdit,
  onHistory,
  onCancelEdit,
  onCloseHistory,
  onChanged,
}: PromptTaskGroupProps) {
  const globalPrompt = prompts.find((prompt) => prompt.layer_id === null) ?? prompts[0]
  const existingLayerIds = new Set(prompts.flatMap((prompt) => (prompt.layer_id === null ? [] : [prompt.layer_id])))
  const availableLayers = layers.filter((layer) => layer.name !== 'Need' && !existingLayerIds.has(layer.id))
  const addKey = `${task}:add-layer`

  return (
    <li className="rounded-md border border-neutral-200 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold text-neutral-950">{task}</p>
        <button
          className="rounded border border-neutral-300 px-2 py-1 text-xs"
          disabled={availableLayers.length === 0}
          onClick={() => onEdit(addKey)}
          type="button"
        >
          Add layer variant
        </button>
      </div>
      <div className="mt-3 space-y-3">
        {prompts.map((prompt) => {
          const key = slotKey(prompt)
          return (
            <div className="rounded-md border border-neutral-200 p-3" key={key}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-neutral-950">{prompt.name}</p>
                  <p className="text-xs text-neutral-500">
                    {scopeLabel(prompt)} · v{prompt.version} · updated {prompt.updated_at}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    className="rounded border border-neutral-300 px-2 py-1 text-xs"
                    onClick={() => onEdit(key)}
                    type="button"
                  >
                    Edit
                  </button>
                  <button
                    className="rounded border border-neutral-300 px-2 py-1 text-xs"
                    onClick={() => onHistory(key)}
                    type="button"
                  >
                    History
                  </button>
                </div>
              </div>
              {prompt.description && <p className="mt-2 text-sm text-neutral-600">{prompt.description}</p>}
              <details className="mt-2">
                <summary className="cursor-pointer text-xs font-medium text-neutral-700">Template</summary>
                <pre className="mt-2 max-h-56 overflow-auto rounded bg-neutral-50 p-3 text-xs text-neutral-800">
                  {prompt.template}
                </pre>
              </details>
              {editingKey === key ? (
                <PromptEditor prompt={prompt} onCancel={onCancelEdit} onSaved={onChanged} />
              ) : null}
              {historyKey === key ? (
                <PromptHistory task={prompt.task} onClose={onCloseHistory} onPromoted={onChanged} />
              ) : null}
            </div>
          )
        })}
      </div>
      {editingKey === addKey ? (
        <PromptEditor
          prompt={globalPrompt}
          mode="add-layer"
          layerOptions={availableLayers}
          onCancel={onCancelEdit}
          onSaved={onChanged}
        />
      ) : null}
    </li>
  )
}
