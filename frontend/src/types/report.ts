export type ReportType =
  | 'out_of_order'
  | 'overflowing'
  | 'dirty'
  | 'closed'
  | 'damaged'
  | 'vandalized'
  | 'other'

export type ReportStatus = 'active' | 'resolved' | 'expired' | 'dismissed'

export interface Report {
  id: string
  poi_id: string
  reporter_id: string
  report_type: ReportType
  description: string | null
  photo_url: string | null
  status: ReportStatus
  confirmation_count: number
  resolved_at: string | null
  resolved_by: string | null
  resolution_note: string | null
  expires_at: string
  created_at: string
  updated_at: string
}

export const REPORT_TYPE_LABELS: Record<ReportType, string> = {
  out_of_order: '고장',
  overflowing: '꽉 참',
  dirty: '더러움',
  closed: '닫힘',
  damaged: '파손',
  vandalized: '훼손',
  other: '기타',
}

export const REPORT_TYPE_ICONS: Record<ReportType, string> = {
  out_of_order: '⛔',
  overflowing: '🗑️',
  dirty: '💩',
  closed: '🔒',
  damaged: '🔨',
  vandalized: '✏️',
  other: '❓',
}

export const ALL_REPORT_TYPES: ReportType[] = [
  'out_of_order',
  'overflowing',
  'dirty',
  'closed',
  'damaged',
  'vandalized',
  'other',
]

// Notifications

export type NotificationType =
  | 'report_resolved'
  | 'report_expired'
  | 'poi_verified'

export interface Notification {
  id: string
  type: NotificationType
  payload: Record<string, unknown>
  read_at: string | null
  created_at: string
}
