import { useCallback, useEffect, useState } from 'react'

const PARAM = 'poi'

/**
 * Track the ``?poi=<uuid>`` URL query param. Two-way: the panel can set it
 * (replaceState — no nav stack pollution), and external nav (back/forward)
 * is reflected via popstate.
 */
export function usePoiUrlParam(): [string | null, (id: string | null) => void] {
  const [poiId, setPoiId] = useState<string | null>(() => readParam())

  useEffect(() => {
    const onPop = () => setPoiId(readParam())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const set = useCallback((id: string | null) => {
    const url = new URL(window.location.href)
    if (id) url.searchParams.set(PARAM, id)
    else url.searchParams.delete(PARAM)
    window.history.replaceState({}, '', url.toString())
    setPoiId(id)
  }, [])

  return [poiId, set]
}

function readParam(): string | null {
  if (typeof window === 'undefined') return null
  return new URLSearchParams(window.location.search).get(PARAM)
}
