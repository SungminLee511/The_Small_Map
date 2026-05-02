import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { POIDetailPanel, formatAttributes } from '@/features/map/POIDetailPanel'
import type { POIDetail } from '@/types/poi'

const fakePoi: POIDetail = {
  id: '11111111-1111-1111-1111-111111111111',
  poi_type: 'toilet',
  location: { lat: 37.5, lng: 126.9 },
  name: '마포구청 화장실',
  attributes: {
    accessibility: true,
    gender: 'separate',
    is_free: true,
    has_baby_changing: true,
    opening_hours: '09:00-18:00',
  },
  source: 'seoul.public_toilets',
  status: 'active',
  external_id: 'EXT-1',
  last_verified_at: '2026-04-30T00:00:00Z',
  verification_count: 3,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-04-30T00:00:00Z',
}

vi.mock('@/api/pois', () => ({
  fetchPOI: vi.fn(),
}))

import { fetchPOI } from '@/api/pois'

function renderWithQuery(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

describe('formatAttributes', () => {
  it('formats toilet attributes', () => {
    const lines = formatAttributes('toilet', {
      accessibility: true,
      gender: 'separate',
      is_free: true,
      has_baby_changing: true,
      opening_hours: '09:00-18:00',
    })
    expect(lines).toContain('♿ 장애인용')
    expect(lines).toContain('남녀 분리')
    expect(lines).toContain('무료')
    expect(lines).toContain('기저귀 교환대')
    expect(lines.some((l) => l.includes('09:00-18:00'))).toBe(true)
  })

  it('formats smoking_area enclosed', () => {
    expect(formatAttributes('smoking_area', { enclosed: true })).toContain(
      '실내/폐쇄형',
    )
  })

  it('returns empty when nothing applicable', () => {
    expect(formatAttributes('bench', {})).toEqual([])
  })
})

describe('POIDetailPanel', () => {
  beforeEach(() => {
    vi.mocked(fetchPOI).mockReset()
  })

  it('renders nothing when poiId is null', () => {
    const { queryByTestId } = renderWithQuery(
      <POIDetailPanel poiId={null} onClose={vi.fn()} />,
    )
    expect(queryByTestId('poi-detail-panel')).toBeNull()
  })

  it('renders POI data when fetch resolves', async () => {
    vi.mocked(fetchPOI).mockResolvedValue(fakePoi)
    renderWithQuery(<POIDetailPanel poiId={fakePoi.id} onClose={vi.fn()} />)
    expect(await screen.findByText('마포구청 화장실')).toBeInTheDocument()
    expect(screen.getByText(/data\.go\.kr/)).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('calls onClose when close button is clicked', async () => {
    vi.mocked(fetchPOI).mockResolvedValue(fakePoi)
    const onClose = vi.fn()
    renderWithQuery(<POIDetailPanel poiId={fakePoi.id} onClose={onClose} />)
    await waitFor(() => screen.getByText('마포구청 화장실'))
    fireEvent.click(screen.getByLabelText('Close detail panel'))
    expect(onClose).toHaveBeenCalled()
  })

  it('calls onClose on Escape', async () => {
    vi.mocked(fetchPOI).mockResolvedValue(fakePoi)
    const onClose = vi.fn()
    renderWithQuery(<POIDetailPanel poiId={fakePoi.id} onClose={onClose} />)
    await waitFor(() => screen.getByText('마포구청 화장실'))
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })
})
