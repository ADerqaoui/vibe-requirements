import { useState } from 'react'
import { NeedList } from './components/NeedList'
import { ProjectList } from './components/ProjectList'
import { SettingsPanel } from './components/SettingsPanel'

export function App() {
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)
  const [costRefreshSignal, setCostRefreshSignal] = useState(0)

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <div className="flex min-h-screen">
        <ProjectList
          onSelectProject={setSelectedProjectId}
          selectedProjectId={selectedProjectId}
        />
        <main className="flex-1 p-6">
          <NeedList
            onSuccessfulGeneration={() => setCostRefreshSignal((currentSignal) => currentSignal + 1)}
            projectId={selectedProjectId}
          />
          <SettingsPanel costRefreshSignal={costRefreshSignal} />
        </main>
      </div>
    </div>
  )
}
