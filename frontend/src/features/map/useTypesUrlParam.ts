import { useCallback, useEffect, useState } from 'react'
import { ALL_POI_TYPES } from '@/types/poi'
import type { POIType } from '@/types/poi'

const PARAM = 'types'
const VALID = new Set<POIType>(ALL_POI_TYPES)

/**
 * Sync the active POI-type filter set with ``?types=toilet,bench`` in the URL.
 * - Missing param → all types active.
 * - Empty value (``?types=``) → none active.
 * - Unknown values are silently dropped.
 *
 * Uses ``replaceState`` so the URL is shareable but the browser back/forward
 * stack isn't polluted.
 */
export function useTypesUrlParam(): [POIType[], (next: POIType[]) => void] {
  const [types, setTypes] = useState<POIType[]>(() => readParam())

  useEffect(() => {
    const onPop = () => setTypes(readParam())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const set = useCallback((next: POIType[]) => {
    const url = new URL(window.location.href)
    if (next.length === ALL_POI_TYPES.length) {
      // "all selected" is the implicit default — drop the param entirely
      url.searchParams.delete(PARAM)
    } else {
      url.searchParams.set(PARAM, next.join(','))
    }
    window.history.replaceState({}, '', url.toString())
    setTypes(next)
  }, [])

  return [types, set]
}

function readParam(): POIType[] {
  if (typeof window === 'undefined') return [...ALL_POI_TYPES]
  const raw = new URLSearchParams(window.location.search).get(PARAM)
  if (raw === null) return [...ALL_POI_TYPES]
  if (raw === '') return []
  const parts = raw.split(',').map((s) => s.trim()).filter(Boolean)
  return parts.filter((p): p is POIType => VALID.has(p as POIType))
}
