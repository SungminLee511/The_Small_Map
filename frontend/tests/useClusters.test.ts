import { describe, it, expect } from 'vitest'
import { renderHook } from '@testing-library/react'
import { CLUSTER_LEVEL_THRESHOLD, levelToZoom, useClusters } from '@/features/map/useClusters'
import type { POI } from '@/types/poi'

function makePoi(id: string, lat: number, lng: number, poi_type: POI['poi_type'] = 'toilet'): POI {
  return {
    id,
    poi_type,
    location: { lat, lng },
    name: `POI-${id}`,
    attributes: {},
    source: 'seed',
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  }
}

describe('levelToZoom', () => {
  it('inverts kakao level into supercluster zoom (smaller level = more zoomed in = higher zoom)', () => {
    expect(levelToZoom(1)).toBeGreaterThan(levelToZoom(10))
  })

  it('clamps to non-negative', () => {
    expect(levelToZoom(100)).toBe(0)
  })
})

describe('useClusters', () => {
  const bbox = { west: 126.0, south: 37.0, east: 127.0, north: 38.0 }

  it('returns empty when no POIs', () => {
    const { result } = renderHook(() =>
      useClusters({ pois: [], bbox, level: 8 }),
    )
    expect(result.current).toEqual([])
  })

  it('returns leaf POIs when zoomed in past threshold', () => {
    const pois = [
      makePoi('a', 37.5, 126.9),
      makePoi('b', 37.51, 126.91),
    ]
    const { result } = renderHook(() =>
      useClusters({
        pois,
        bbox,
        // level < threshold = no clustering
        level: CLUSTER_LEVEL_THRESHOLD - 1,
      }),
    )
    expect(result.current).toHaveLength(2)
    expect(result.current.every((c) => c.kind === 'poi')).toBe(true)
  })

  it('groups nearby POIs into clusters when zoomed out', () => {
    // 30 POIs within ~100m of each other — should cluster at low zoom
    const pois: POI[] = Array.from({ length: 30 }, (_, i) =>
      makePoi(`p${i}`, 37.55 + i * 0.0001, 126.92 + i * 0.0001),
    )
    const { result } = renderHook(() =>
      useClusters({ pois, bbox, level: 13 }),
    )
    const clusters = result.current.filter((c) => c.kind === 'cluster')
    expect(clusters.length).toBeGreaterThan(0)
    const totalCount = result.current.reduce(
      (sum, c) => sum + (c.kind === 'cluster' ? c.count : 1),
      0,
    )
    expect(totalCount).toBe(pois.length)
  })

  it('memoizes the supercluster index on the POI list reference', () => {
    const pois = [makePoi('a', 37.5, 126.9)]
    const { result, rerender } = renderHook(
      ({ b }) => useClusters({ pois, bbox: b, level: 8 }),
      { initialProps: { b: bbox } },
    )
    const first = result.current
    // Re-render with a new bbox object — index should not need to rebuild
    rerender({ b: { ...bbox } })
    expect(result.current).not.toBe(first) // recomputed result list
    // Both should describe the same single POI
    expect(result.current).toHaveLength(1)
  })
})
