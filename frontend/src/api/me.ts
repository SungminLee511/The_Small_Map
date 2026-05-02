import { apiClient } from './client'
import type { POIDetail } from '@/types/poi'

export async function fetchMySubmissions(): Promise<POIDetail[]> {
  const { data } = await apiClient.get<POIDetail[]>('/me/submissions', {
    params: { include_deleted: false, limit: 100 },
  })
  return data
}

export async function fetchMyConfirmations(): Promise<POIDetail[]> {
  const { data } = await apiClient.get<POIDetail[]>('/me/confirmations', {
    params: { limit: 100 },
  })
  return data
}
