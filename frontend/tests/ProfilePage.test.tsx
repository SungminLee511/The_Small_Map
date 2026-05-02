import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ProfilePage } from '@/features/profile/ProfilePage'
import type { POIDetail } from '@/types/poi'
import type { UserMe } from '@/types/user'

vi.mock('@/api/auth', async () => {
  const actual = await vi.importActual<typeof import('@/api/auth')>('@/api/auth')
  return { ...actual, fetchMe: vi.fn() }
})
vi.mock('@/api/me', () => ({
  fetchMySubmissions: vi.fn(),
  fetchMyConfirmations: vi.fn(),
}))

import { fetchMe } from '@/api/auth'
import { fetchMyConfirmations, fetchMySubmissions } from '@/api/me'

function renderWithQuery(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

const ME: UserMe = {
  id: '11111111-1111-1111-1111-111111111111',
  display_name: 'Sungmin',
  email: 'a@b.c',
  avatar_url: null,
  is_admin: false,
  reputation: 12,
}

const submission: POIDetail = {
  id: '22222222-2222-2222-2222-222222222222',
  poi_type: 'toilet',
  location: { lat: 37.5, lng: 126.9 },
  name: '내가 만든 화장실',
  attributes: {},
  source: `user:${ME.id}`,
  status: 'active',
  verification_status: 'unverified',
  external_id: null,
  last_verified_at: null,
  verification_count: 1,
  created_at: '2026-04-30T00:00:00Z',
  updated_at: '2026-04-30T00:00:00Z',
}

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.mocked(fetchMe).mockReset()
    vi.mocked(fetchMySubmissions).mockReset()
    vi.mocked(fetchMyConfirmations).mockReset()
  })

  it('shows login link when logged out', async () => {
    vi.mocked(fetchMe).mockResolvedValue(null)
    renderWithQuery(<ProfilePage />)
    expect(await screen.findByTestId('profile-login-link')).toBeInTheDocument()
  })

  it('shows reputation and submissions when logged in', async () => {
    vi.mocked(fetchMe).mockResolvedValue(ME)
    vi.mocked(fetchMySubmissions).mockResolvedValue([submission])
    vi.mocked(fetchMyConfirmations).mockResolvedValue([])
    renderWithQuery(<ProfilePage />)

    expect(await screen.findByText('Sungmin')).toBeInTheDocument()
    expect(screen.getByTestId('profile-reputation').textContent).toContain('12')
    expect(await screen.findByText('내가 만든 화장실')).toBeInTheDocument()
    expect(screen.getByText('미확인')).toBeInTheDocument()
  })

  it('shows empty messages when nothing submitted', async () => {
    vi.mocked(fetchMe).mockResolvedValue(ME)
    vi.mocked(fetchMySubmissions).mockResolvedValue([])
    vi.mocked(fetchMyConfirmations).mockResolvedValue([])
    renderWithQuery(<ProfilePage />)
    expect(
      await screen.findByText('아직 등록한 장소가 없습니다.'),
    ).toBeInTheDocument()
    expect(
      screen.getByText('아직 확인한 장소가 없습니다.'),
    ).toBeInTheDocument()
  })
})
