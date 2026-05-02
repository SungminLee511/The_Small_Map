export type POIType = 'toilet' | 'trash_can' | 'bench' | 'smoking_area' | 'water_fountain'

export interface LatLng {
  lat: number
  lng: number
}

export interface POI {
  id: string
  poi_type: POIType
  location: LatLng
  name: string | null
  attributes: Record<string, unknown> | null
  source: string
  status: string
  verification_status?: 'unverified' | 'verified'
  /** Phase 3.3.3 — count of active issue reports */
  active_report_count?: number
  created_at: string
  updated_at: string
}

import type { Report } from './report'

export interface POIDetail extends POI {
  external_id: string | null
  last_verified_at: string | null
  verification_count: number
  /** Phase 3.3.3 — most-recent active reports (max 5) */
  active_reports?: Report[]
}

export interface POIListResponse {
  items: POI[]
  truncated: boolean
}

export interface BBox {
  west: number
  south: number
  east: number
  north: number
}

export const POI_TYPE_LABELS: Record<POIType, string> = {
  toilet: '화장실',
  trash_can: '쓰레기통',
  bench: '벤치',
  smoking_area: '흡연구역',
  water_fountain: '음수대',
}

export const POI_TYPE_ICONS: Record<POIType, string> = {
  toilet: '🚻',
  trash_can: '🗑️',
  bench: '🪑',
  smoking_area: '🚬',
  water_fountain: '🚰',
}

export const ALL_POI_TYPES: POIType[] = [
  'toilet', 'trash_can', 'bench', 'smoking_area', 'water_fountain',
]
