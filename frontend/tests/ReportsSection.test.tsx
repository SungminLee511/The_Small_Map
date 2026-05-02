import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReportsSection } from '@/features/reports/ReportsSection'
import type { POIDetail } from '@/types/poi'
import type { Report } from '@/types/report'

vi.mock('@/api/auth', async () => {
  const actual = await vi.importActual<typeof import('@/api/auth')>('@/api/auth')
  return { ...actual, fetchMe: vi.fn() }
})
vi.mock('@/api/reports', () => ({
  fetchReportsForPOI: vi.fn(),
  confirmReport: vi.fn(),
}))

import { fetchMe } from '@/api/auth'
import { confirmReport, fetchReportsForPOI } from '@/api/reports'

function renderSection(poi: POIDetail) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <ReportsSection poi={poi} />
    </QueryClientProvider>,
  )
}

const baseReport: Report = {
  id: 'r-1',
  poi_id: 'p-1',
  reporter_id: 'someone-else',
  report_type: 'dirty',
  description: 'gross',
  photo_url: null,
  status: 'active',
  confirmation_count: 1,
  resolved_at: null,
  resolved_by: null,
  resolution_note: null,
  expires_at: '2026-05-09T00:00:00Z',
  created_at: '2026-05-02T00:00:00Z',
  updated_at: '2026-05-02T00:00:00Z',
}

const basePoi: POIDetail = {
  id: 'p-1',
  poi_type: 'toilet',
  location: { lat: 37.5, lng: 126.9 },
  name: 'T',
  attributes: {},
  source: 'seed',
  status: 'active',
  external_id: null,
  last_verified_at: null,
  verification_count: 1,
  created_at: '2026-04-01T00:00:00Z',
  updated_at: '2026-04-30T00:00:00Z',
  active_reports: [],
}

describe('ReportsSection', () => {
  beforeEach(() => {
    vi.mocked(fetchMe).mockReset()
    vi.mocked(fetchReportsForPOI).mockReset()
    vi.mocked(confirmReport).mockReset()
  })

  it('shows empty state when no active_reports preloaded', () => {
    vi.mocked(fetchMe).mockResolvedValue(null)
    vi.mocked(fetchReportsForPOI).mockResolvedValue([])
    renderSection(basePoi)
    expect(screen.getByTestId('reports-empty')).toBeInTheDocument()
  })

  it('renders preloaded active_reports immediately', () => {
    vi.mocked(fetchMe).mockResolvedValue(null)
    vi.mocked(fetchReportsForPOI).mockResolvedValue([baseReport])
    renderSection({ ...basePoi, active_reports: [baseReport] })
    expect(screen.getByText('더러움')).toBeInTheDocument()
    expect(screen.getByText('gross')).toBeInTheDocument()
  })

  it('hides "신고하기" button when logged out', async () => {
    vi.mocked(fetchMe).mockResolvedValue(null)
    vi.mocked(fetchReportsForPOI).mockResolvedValue([])
    renderSection(basePoi)
    await waitFor(() => {
      expect(screen.queryByTestId('open-report-modal-button')).toBeNull()
    })
  })

  it('shows "신고하기" button when logged in', async () => {
    vi.mocked(fetchMe).mockResolvedValue({
      id: 'me',
      display_name: 'M',
      email: null,
      avatar_url: null,
      is_admin: false,
      reputation: 0,
    })
    vi.mocked(fetchReportsForPOI).mockResolvedValue([])
    renderSection(basePoi)
    expect(
      await screen.findByTestId('open-report-modal-button'),
    ).toBeInTheDocument()
  })

  it('confirm button fires confirmReport for other users', async () => {
    vi.mocked(fetchMe).mockResolvedValue({
      id: 'me',
      display_name: 'M',
      email: null,
      avatar_url: null,
      is_admin: false,
      reputation: 0,
    })
    vi.mocked(fetchReportsForPOI).mockResolvedValue([baseReport])
    vi.mocked(confirmReport).mockResolvedValue({
      report_id: baseReport.id,
      confirmation_count: 2,
    })
    renderSection({ ...basePoi, active_reports: [baseReport] })
    fireEvent.click(await screen.findByTestId('confirm-report-button'))
    await waitFor(() => expect(confirmReport).toHaveBeenCalledWith('r-1'))
  })

  it('confirm button is disabled for own report', async () => {
    vi.mocked(fetchMe).mockResolvedValue({
      id: 'someone-else', // Same as baseReport.reporter_id
      display_name: 'M',
      email: null,
      avatar_url: null,
      is_admin: false,
      reputation: 0,
    })
    vi.mocked(fetchReportsForPOI).mockResolvedValue([baseReport])
    renderSection({ ...basePoi, active_reports: [baseReport] })
    const btn = (await screen.findByTestId(
      'confirm-report-button',
    )) as HTMLButtonElement
    expect(btn.disabled).toBe(true)
    expect(btn.textContent).toContain('내 신고')
  })
})
