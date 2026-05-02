import { apiClient } from './client'
import type { Notification, Report, ReportType } from '@/types/report'

export interface ReportListResponse {
  items: Report[]
  truncated: boolean
}

export async function fetchReportsForPOI(poiId: string): Promise<Report[]> {
  const { data } = await apiClient.get<ReportListResponse>(
    `/pois/${poiId}/reports`,
    { params: { status: 'active' } },
  )
  return data.items
}

export async function submitReport(
  poiId: string,
  body: { report_type: ReportType; description?: string | null; photo_url?: string | null },
): Promise<Report> {
  const { data } = await apiClient.post<Report>(`/pois/${poiId}/reports`, body)
  return data
}

export async function confirmReport(
  reportId: string,
): Promise<{ report_id: string; confirmation_count: number }> {
  const { data } = await apiClient.post(`/reports/${reportId}/confirm`)
  return data
}

export async function resolveReport(
  reportId: string,
  body: { resolution_note: string; photo_url?: string | null },
): Promise<Report> {
  const { data } = await apiClient.post<Report>(`/reports/${reportId}/resolve`, body)
  return data
}

// Notifications

export async function fetchNotifications(opts?: {
  onlyUnread?: boolean
  limit?: number
}): Promise<Notification[]> {
  const { data } = await apiClient.get<Notification[]>('/notifications', {
    params: {
      only_unread: opts?.onlyUnread ?? false,
      limit: opts?.limit ?? 50,
    },
  })
  return data
}

export async function fetchUnreadCount(): Promise<number> {
  const { data } = await apiClient.get<{ unread: number }>(
    '/notifications/unread-count',
  )
  return data.unread
}

export async function markNotificationRead(id: string): Promise<void> {
  await apiClient.post(`/notifications/${id}/read`)
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.post('/notifications/read-all')
}
