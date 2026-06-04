import { useEffect, useState } from 'react'
import { fetchSettings } from '../api/settings'

export function useRouterEnabled(onError: (error: unknown) => void) {
  const [routerEnabled, setRouterEnabled] = useState(false)

  useEffect(() => {
    fetchSettings()
      .then((settings) => setRouterEnabled(settings.router_enabled))
      .catch((error: unknown) => {
        onError(error)
        setRouterEnabled(false)
      })
  }, [onError])

  return { routerEnabled, setRouterEnabled }
}
