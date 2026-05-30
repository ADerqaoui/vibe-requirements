import { useEffect, useState } from 'react'
import { fetchHealth, type HealthStatus } from './api/health'

export function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err) => setError(String(err)))
  }, [])

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900 flex items-center justify-center">
      <div className="rounded-xl border border-neutral-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold">Requirement Review Dashboard</h1>
        <p className="mt-1 text-sm text-neutral-500">Slice 1 — scaffold</p>
        <div className="mt-4 text-sm">
          {error && <span className="text-red-600">Backend unreachable: {error}</span>}
          {!error && !health && <span className="text-neutral-400">Checking backend…</span>}
          {health && (
            <ul className="space-y-1">
              <li>API: <b>{health.status}</b></li>
              <li>Database: <b>{health.database}</b></li>
              <li>Ollama: <b>{health.ollama}</b></li>
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
