import { ProjectList } from './components/ProjectList'

export function App() {
  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <div className="flex min-h-screen">
        <ProjectList />
        <main className="flex-1 p-6">
          <div className="text-sm text-neutral-500">Needs and specs arrive in later slices.</div>
        </main>
      </div>
    </div>
  )
}
