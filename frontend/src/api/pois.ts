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
