import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell } from 'lucide-react'
import {
  fetchNotifications,
  fetchUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '@/api/reports'
import { useMe } from '@/features/auth/useMe'
import type { Notification } from '@/types/report'

const POLL_MS = 60_000

/**
 * Bell icon with unread badge + dropdown listing recent notifications.
 * Polls /notifications/unread-count once a minute while authenticated.
 * Clicking a notification marks it read and navigates to the relevant POI.
 */
export function NotificationsBell() {
  const { data: me } = useMe()
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement | null>(null)
  const qc = useQueryClient()

  const unreadQ = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: fetchUnreadCount,
    enabled: !!me,
    refetchInterval: POLL_MS,
    refetchOnWindowFocus: true,
    staleTime: POLL_MS,
  })

  const listQ = useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: () => fetchNotifications({ limit: 30 }),
    enabled: !!me && open,
    staleTime: 15_000,
  })

  const markOneMut = useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications', 'unread-count'] })
      qc.invalidateQueries({ queryKey: ['notifications', 'list'] })
    },
  })
  const markAllMut = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications', 'unread-count'] })
      qc.invalidateQueries({ queryKey: ['notifications', 'list'] })
    },
  })

  // Click-outside to close
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  if (!me) return null

  const unread = unreadQ.data ?? 0

  const onClickItem = (n: Notification) => {
    if (n.read_at === null) markOneMut.mutate(n.id)
    const poiId =
      typeof n.payload?.poi_id === 'string' ? n.payload.poi_id : null
    if (poiId) {
      // Update URL — MapView reacts to ?poi= and opens the detail panel
      const url = new URL(window.location.href)
      url.searchParams.set('poi', poiId)
      // Drop /me if the user is currently on the profile page
      if (url.pathname === '/me') url.pathname = '/'
      window.history.pushState({}, '', url.toString())
      // Force a soft reload of the route — App.tsx listens for popstate
      window.dispatchEvent(new PopStateEvent('popstate'))
      setOpen(false)
    }
  }

  return (
    <div className="relative inline-block" ref={wrapRef}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label="알림"
        data-testid="notifications-bell"
        className="relative w-9 h-9 inline-flex items-center justify-center rounded-full bg-white/90 backdrop-blur shadow-md text-gray-700 hover:text-gray-900"
      >
        <Bell size={18} aria-hidden="true" />
        {unread > 0 && (
          <span
            data-testid="notifications-unread-badge"
            className="absolute -top-1 -right-1 bg-red-600 text-white text-[10px] font-bold rounded-full min-w-4 h-4 px-1 flex items-center justify-center border border-white"
          >
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          role="menu"
          data-testid="notifications-dropdown"
          className="absolute right-0 mt-2 w-80 max-h-96 overflow-y-auto bg-white rounded-xl shadow-2xl border border-gray-200 z-30"
        >
          <header className="px-3 py-2 flex items-center justify-between border-b border-gray-100">
            <h3 className="text-sm font-semibold">알림</h3>
            <button
              type="button"
              onClick={() => markAllMut.mutate()}
              disabled={markAllMut.isPending || unread === 0}
              data-testid="notifications-mark-all-read"
              className="text-xs text-blue-600 hover:underline disabled:opacity-40 disabled:no-underline"
            >
              모두 읽음
            </button>
          </header>

          {listQ.isLoading && (
            <p className="px-3 py-3 text-sm text-gray-500">로딩 중…</p>
          )}
          {listQ.data && listQ.data.length === 0 && (
            <p className="px-3 py-3 text-sm text-gray-500">
              알림이 없습니다.
            </p>
          )}
          {listQ.data && listQ.data.length > 0 && (
            <ul>
              {listQ.data.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    onClick={() => onClickItem(n)}
                    data-testid="notification-item"
                    data-notification-id={n.id}
                    data-read={n.read_at !== null ? 'true' : 'false'}
                    className={`w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100 ${
                      n.read_at === null ? 'bg-blue-50/40' : ''
                    }`}
                  >
                    <div className="text-sm font-medium">
                      {labelFor(n.type)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {timeAgo(n.created_at)}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}

function labelFor(type: Notification['type']): string {
  switch (type) {
    case 'report_resolved':
      return '신고가 해결되었습니다'
    case 'report_expired':
      return '신고가 만료되었습니다'
    case 'poi_verified':
      return '제출한 POI가 확인되었습니다'
  }
}

function timeAgo(iso: string): string {
  const ts = new Date(iso).getTime()
  if (Number.isNaN(ts)) return iso
  const elapsed = (Date.now() - ts) / 1000
  if (elapsed < 60) return '방금'
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}분 전`
  if (elapsed < 86400) return `${Math.floor(elapsed / 3600)}시간 전`
  return `${Math.floor(elapsed / 86400)}일 전`
}
