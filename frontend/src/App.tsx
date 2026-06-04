import { useCallback, useState } from 'react'
import { NeedList } from './components/NeedList'
import { ProjectList } from './components/ProjectList'
import { SettingsPanel } from './components/SettingsPanel'
import { useRouterEnabled } from './hooks/useRouterEnabled'

export function App() {
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)
  const [costRefreshSignal, setCostRefreshSignal] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const handleRouterError = useCallback((loadError: unknown) => {
    setError(loadError instanceof Error ? loadError.message : String(loadError))
  }, [])
  const { routerEnabled, setRouterEnabled } = useRouterEnabled(handleRouterError)

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <div className="flex min-h-screen">
        <ProjectList
          onSelectProject={setSelectedProjectId}
          selectedProjectId={selectedProjectId}
        />
        <main className="flex-1 p-6">
          {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
          <NeedList
            onSuccessfulGeneration={() => setCostRefreshSignal((currentSignal) => currentSignal + 1)}
            projectId={selectedProjectId}
            routerEnabled={routerEnabled}
          />
          <SettingsPanel
            costRefreshSignal={costRefreshSignal}
            routerEnabled={routerEnabled}
            setRouterEnabled={setRouterEnabled}
          />
        </main>
      </div>
    </div>
  )
}
