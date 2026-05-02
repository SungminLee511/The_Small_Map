import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { NotificationsBell } from '@/features/notifications/NotificationsBell'

vi.mock('@/api/auth', async () => {
  const actual = await vi.importActual<typeof import('@/api/auth')>('@/api/auth')
  return { ...actual, fetchMe: vi.fn() }
})
vi.mock('@/api/reports', () => ({
  fetchUnreadCount: vi.fn(),
  fetchNotifications: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}))

import { fetchMe } from '@/api/auth'
import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/api/reports'

const me = {
  id: 'me-1',
  display_name: 'M',
  email: null,
  avatar_url: null,
  is_admin: false,
  reputation: 0,
}

function renderBell() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <NotificationsBell />
    </QueryClientProvider>,
  )
}

describe('NotificationsBell', () => {
  beforeEach(() => {
    vi.mocked(fetchMe).mockReset()
    vi.mocked(fetchUnreadCount).mockReset()
    vi.mocked(fetchNotifications).mockReset()
    vi.mocked(markNotificationRead).mockReset()
    vi.mocked(markAllNotificationsRead).mockReset()
  })

  it('renders nothing when logged out', async () => {
    vi.mocked(fetchMe).mockResolvedValue(null)
    const { queryByTestId } = renderBell()
    await waitFor(() =>
      expect(queryByTestId('notifications-bell')).toBeNull(),
    )
  })

  it('shows unread badge when count > 0', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    vi.mocked(fetchUnreadCount).mockResolvedValue(3)
    renderBell()
    await waitFor(() =>
      expect(screen.getByTestId('notifications-bell')).toBeInTheDocument(),
    )
    const badge = await screen.findByTestId('notifications-unread-badge')
    expect(badge).toHaveTextContent('3')
  })

  it('opens dropdown and lists notifications when clicked', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    vi.mocked(fetchUnreadCount).mockResolvedValue(1)
    vi.mocked(fetchNotifications).mockResolvedValue([
      {
        id: 'n-1',
        type: 'report_resolved',
        payload: { poi_id: 'p-1', report_id: 'r-1' },
        read_at: null,
        created_at: '2026-05-02T00:00:00Z',
      },
    ])
    renderBell()
    await waitFor(() => screen.getByTestId('notifications-bell'))
    fireEvent.click(screen.getByTestId('notifications-bell'))
    expect(
      await screen.findByTestId('notifications-dropdown'),
    ).toBeInTheDocument()
    expect(
      await screen.findByText('신고가 해결되었습니다'),
    ).toBeInTheDocument()
  })

  it('clicking an unread item marks it read and updates URL', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    vi.mocked(fetchUnreadCount).mockResolvedValue(1)
    vi.mocked(fetchNotifications).mockResolvedValue([
      {
        id: 'n-1',
        type: 'poi_verified',
        payload: { poi_id: 'p-1' },
        read_at: null,
        created_at: '2026-05-02T00:00:00Z',
      },
    ])
    vi.mocked(markNotificationRead).mockResolvedValue(undefined)

    renderBell()
    await waitFor(() => screen.getByTestId('notifications-bell'))
    fireEvent.click(screen.getByTestId('notifications-bell'))
    fireEvent.click(await screen.findByTestId('notification-item'))
    await waitFor(() => expect(markNotificationRead).toHaveBeenCalledWith('n-1'))
    expect(new URL(window.location.href).searchParams.get('poi')).toBe('p-1')
  })

  it('"모두 읽음" calls markAllNotificationsRead', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    vi.mocked(fetchUnreadCount).mockResolvedValue(2)
    vi.mocked(fetchNotifications).mockResolvedValue([])
    vi.mocked(markAllNotificationsRead).mockResolvedValue(undefined)
    renderBell()
    await waitFor(() => screen.getByTestId('notifications-bell'))
    fireEvent.click(screen.getByTestId('notifications-bell'))
    fireEvent.click(
      await screen.findByTestId('notifications-mark-all-read'),
    )
    await waitFor(() => expect(markAllNotificationsRead).toHaveBeenCalled())
  })
})
