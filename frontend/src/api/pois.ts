import { apiClient } from './client'
import type { BBox, POIDetail, POIListResponse, POIType } from '@/types/poi'

export async function fetchPOIs(bbox: BBox, types?: POIType[]): Promise<POIListResponse> {
  const bboxStr = `${bbox.west},${bbox.south},${bbox.east},${bbox.north}`
  const params: Record<string, string | string[]> = { bbox: bboxStr }
  if (types && types.length > 0) {
    params.type = types
  }
  const { data } = await apiClient.get<POIListResponse>('/pois', { params })
  return data
}

export async function fetchPOI(id: string): Promise<POIDetail> {
  const { data } = await apiClient.get<POIDetail>(`/pois/${id}`)
  return data
}

export interface ConfirmResponse {
  poi_id: string
  verification_count: number
  verification_status: 'unverified' | 'verified'
  flipped_to_verified: boolean
}

export async function confirmPOI(id: string): Promise<ConfirmResponse> {
  const { data } = await apiClient.post<ConfirmResponse>(`/pois/${id}/confirm`)
  return data
}
