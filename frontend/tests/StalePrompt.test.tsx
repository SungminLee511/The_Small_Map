import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StalePrompt } from '@/features/map/StalePrompt'
import type { POIDetail } from '@/types/poi'

vi.mock('@/api/auth', async () => {
  const actual = await vi.importActual<typeof import('@/api/auth')>('@/api/auth')
  return { ...actual, fetchMe: vi.fn() }
})
vi.mock('@/api/pois', () => ({
  confirmPOI: vi.fn(),
  proposeRemoval: vi.fn(),
  fetchPOI: vi.fn(),
  fetchPOIs: vi.fn(),
}))

import { fetchMe } from '@/api/auth'
import { confirmPOI, proposeRemoval } from '@/api/pois'

const me = {
  id: 'me-1',
  display_name: 'M',
  email: null,
  avatar_url: null,
  is_admin: false,
  reputation: 5,
}

const stalePoi: POIDetail = {
  id: 'p-1',
  poi_type: 'toilet',
  location: { lat: 37.5, lng: 126.9 },
  name: 'Stale',
  attributes: {},
  source: 'seoul.public_toilets',
  status: 'active',
  is_stale: true,
  external_id: null,
  last_verified_at: '2025-09-01T00:00:00Z',
  verification_count: 1,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-09-01T00:00:00Z',
}

function renderPrompt(overrides?: Partial<POIDetail>) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <StalePrompt poi={{ ...stalePoi, ...overrides }} />
    </QueryClientProvider>,
  )
}

describe('StalePrompt', () => {
  beforeEach(() => {
    vi.mocked(fetchMe).mockReset()
    vi.mocked(confirmPOI).mockReset()
    vi.mocked(proposeRemoval).mockReset()
  })

  it('renders nothing when not stale', () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    const { queryByTestId } = renderPrompt({ is_stale: false })
    expect(queryByTestId('stale-prompt')).toBeNull()
  })

  it('renders nothing when logged out', async () => {
    vi.mocked(fetchMe).mockResolvedValue(null)
    renderPrompt()
    await waitFor(() => {
      expect(screen.queryByTestId('stale-prompt')).toBeNull()
    })
  })

  it('renders nothing for own submission', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    renderPrompt({ source: `user:${me.id}` })
    await waitFor(() => {
      expect(screen.queryByTestId('stale-prompt')).toBeNull()
    })
  })

  it('renders both action buttons when stale + logged in + not own', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    renderPrompt()
    expect(await screen.findByTestId('stale-prompt')).toBeInTheDocument()
    expect(screen.getByTestId('stale-confirm-button')).toBeInTheDocument()
    expect(screen.getByTestId('stale-remove-button')).toBeInTheDocument()
  })

  it('confirm button fires confirmPOI', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    vi.mocked(confirmPOI).mockResolvedValue({
      poi_id: 'p-1',
      verification_count: 2,
      verification_status: 'unverified',
      flipped_to_verified: false,
    })
    renderPrompt()
    fireEvent.click(await screen.findByTestId('stale-confirm-button'))
    await waitFor(() => expect(confirmPOI).toHaveBeenCalledWith('p-1'))
  })

  it('remove button fires proposeRemoval and shows count', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    vi.mocked(proposeRemoval).mockResolvedValue({
      poi_id: 'p-1',
      proposal_count: 2,
      threshold: 3,
      soft_deleted: false,
    })
    renderPrompt()
    fireEvent.click(await screen.findByTestId('stale-remove-button'))
    await waitFor(() => expect(proposeRemoval).toHaveBeenCalledWith('p-1'))
    expect(await screen.findByText('제안 2/3')).toBeInTheDocument()
  })

  it('shows "삭제됨" when 3rd proposal soft-deletes', async () => {
    vi.mocked(fetchMe).mockResolvedValue(me)
    vi.mocked(proposeRemoval).mockResolvedValue({
      poi_id: 'p-1',
      proposal_count: 3,
      threshold: 3,
      soft_deleted: true,
    })
    renderPrompt()
    fireEvent.click(await screen.findByTestId('stale-remove-button'))
    await waitFor(() =>
      expect(screen.getByTestId('stale-remove-button')).toHaveTextContent(
        '삭제됨',
      ),
    )
  })
})
