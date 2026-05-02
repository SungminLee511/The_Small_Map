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

export type ReputationEventType =
  | 'poi_submitted_verified'
  | 'poi_submitted_rejected'
  | 'confirmation'
  | 'report_submitted_resolved'
  | 'report_dismissed_admin'
  | 'daily_active'

export interface ReputationEvent {
  id: string
  event_type: ReputationEventType
  delta: number
  ref_id: string | null
  created_at: string
}

export async function fetchMyReputationEvents(): Promise<ReputationEvent[]> {
  const { data } = await apiClient.get<ReputationEvent[]>('/me/reputation', {
    params: { limit: 100 },
  })
  return data
}
