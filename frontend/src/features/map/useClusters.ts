import { useMemo } from 'react'
import Supercluster from 'supercluster'
import type { POI, BBox } from '@/types/poi'

/**
 * Result of clustering: either a leaf POI or a cluster of N points.
 */
export type ClusterPoint =
  | { kind: 'poi'; poi: POI; lat: number; lng: number }
  | {
      kind: 'cluster'
      id: number
      lat: number
      lng: number
      count: number
      // Most-frequent POI type inside the cluster, used for color
      dominantType: POI['poi_type'] | null
    }

const CLUSTER_AT_ZOOM_BELOW = 15
const CLUSTER_RADIUS_PX = 60
const SUPERCLUSTER_MAX_ZOOM = 20

interface UseClustersArgs {
  pois: POI[] | undefined
  bbox: BBox | null
  /** Kakao map "level" (1=closest, 14=farthest). Lower = more zoomed in. */
  level: number
}

/**
 * Convert Kakao Map "level" to a supercluster-style "zoom" integer.
 * Kakao levels run 1–14 (small=zoomed in). Supercluster expects 0–20
 * (small=zoomed out). Map roughly: zoom = max(0, 18 - level).
 */
export function levelToZoom(level: number): number {
  return Math.max(0, Math.min(SUPERCLUSTER_MAX_ZOOM, 18 - level))
}

/**
 * Build clusters from POIs visible inside ``bbox``. Memoizes the supercluster
 * index on the POI list reference, so it only rebuilds when the POI set
 * actually changes — pan/zoom only re-queries the index.
 */
export function useClusters({ pois, bbox, level }: UseClustersArgs): ClusterPoint[] {
  const zoom = levelToZoom(level)
  const shouldCluster = level >= CLUSTER_AT_ZOOM_BELOW

  const index = useMemo(() => {
    if (!pois || pois.length === 0) return null
    const sc = new Supercluster<{ poi: POI }>({
      radius: CLUSTER_RADIUS_PX,
      maxZoom: SUPERCLUSTER_MAX_ZOOM,
    })
    sc.load(
      pois.map((poi) => ({
        type: 'Feature' as const,
        properties: { poi },
        geometry: {
          type: 'Point' as const,
          coordinates: [poi.location.lng, poi.location.lat],
        },
      })),
    )
    return sc
  }, [pois])

  return useMemo<ClusterPoint[]>(() => {
    if (!index || !pois) return []
    if (!shouldCluster || !bbox) {
      // Render every POI as a leaf
      return pois.map((poi) => ({
        kind: 'poi' as const,
        poi,
        lat: poi.location.lat,
        lng: poi.location.lng,
      }))
    }
    const features = index.getClusters(
      [bbox.west, bbox.south, bbox.east, bbox.north],
      zoom,
    )
    return features.map((f): ClusterPoint => {
      const [lng, lat] = f.geometry.coordinates as [number, number]
      const props = f.properties as Record<string, unknown>
      if (props.cluster) {
        const clusterId = props.cluster_id as number
        const count = props.point_count as number
        return {
          kind: 'cluster',
          id: clusterId,
          lat,
          lng,
          count,
          dominantType: dominantTypeIn(index, clusterId, count),
        }
      }
      const poi = (props as { poi: POI }).poi
      return { kind: 'poi', poi, lat, lng }
    })
  }, [index, pois, bbox, zoom, shouldCluster])
}

/**
 * Compute the dominant POI type inside a cluster by walking its leaves.
 * Returns null if the cluster is mixed (no single type > 50% of points).
 */
function dominantTypeIn(
  index: Supercluster<{ poi: POI }>,
  clusterId: number,
  count: number,
): POI['poi_type'] | null {
  // Cap leaves fetched to keep this cheap on huge clusters
  const leaves = index.getLeaves(clusterId, Math.min(count, 100))
  const counts: Partial<Record<POI['poi_type'], number>> = {}
  for (const leaf of leaves) {
    const t = (leaf.properties as { poi: POI }).poi.poi_type
    counts[t] = (counts[t] ?? 0) + 1
  }
  let best: { type: POI['poi_type']; n: number } | null = null
  for (const [t, n] of Object.entries(counts)) {
    if (!best || (n as number) > best.n) best = { type: t as POI['poi_type'], n: n as number }
  }
  if (!best) return null
  return best.n / leaves.length > 0.5 ? best.type : null
}

/** Threshold below which we cluster. Exported for tests. */
export const CLUSTER_LEVEL_THRESHOLD = CLUSTER_AT_ZOOM_BELOW
