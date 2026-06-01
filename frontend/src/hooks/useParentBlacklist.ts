import { useCallback, useState } from 'react'
import { fetchNeedBlacklist, fetchSpecBlacklist } from '../api/blacklist'

type BlacklistParent = {
  kind: 'need' | 'spec'
  id: number
}

type UseParentBlacklistResult = {
  blacklistCount: number
  loadBlacklistCount: (parent: BlacklistParent | null) => Promise<void>
}

export function useParentBlacklist(): UseParentBlacklistResult {
  const [blacklistCount, setBlacklistCount] = useState(0)

  const loadBlacklistCount = useCallback(async (parent: BlacklistParent | null) => {
    if (parent === null) {
      setBlacklistCount(0)
      return
    }
    const entries =
      parent.kind === 'need'
        ? await fetchNeedBlacklist(parent.id)
        : await fetchSpecBlacklist(parent.id)
    setBlacklistCount(entries.length)
  }, [])

  return { blacklistCount, loadBlacklistCount }
}
