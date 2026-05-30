import { useState } from 'react'
import { NeedList } from './components/NeedList'
import { ProjectList } from './components/ProjectList'

export function App() {
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null)

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <div className="flex min-h-screen">
        <ProjectList
          onSelectProject={setSelectedProjectId}
          selectedProjectId={selectedProjectId}
        />
        <main className="flex-1 p-6">
          <NeedList projectId={selectedProjectId} />
        </main>
      </div>
    </div>
  )
}
