import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReportResolveModal } from '@/features/reports/ReportResolveModal'
import type { Report } from '@/types/report'

vi.mock('@/api/reports', () => ({
  resolveReport: vi.fn(),
}))

import { resolveReport } from '@/api/reports'

const r: Report = {
  id: 'r-1',
  poi_id: 'p-1',
  reporter_id: 'u-1',
  report_type: 'dirty',
  description: null,
  photo_url: null,
  status: 'active',
  confirmation_count: 0,
  resolved_at: null,
  resolved_by: null,
  resolution_note: null,
  expires_at: '2026-05-09T00:00:00Z',
  created_at: '2026-05-02T00:00:00Z',
  updated_at: '2026-05-02T00:00:00Z',
}

function renderModal() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onClose = vi.fn()
  return {
    onClose,
    ...render(
      <QueryClientProvider client={qc}>
        <ReportResolveModal report={r} poiId="p-1" onClose={onClose} />
      </QueryClientProvider>,
    ),
  }
}

describe('ReportResolveModal', () => {
  beforeEach(() => {
    vi.mocked(resolveReport).mockReset()
  })

  it('submit disabled until note typed', () => {
    renderModal()
    const btn = screen.getByTestId('resolve-submit-button') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
    fireEvent.change(screen.getByTestId('resolve-note'), {
      target: { value: '치웠음' },
    })
    expect(btn.disabled).toBe(false)
  })

  it('calls resolveReport with trimmed note + photo', async () => {
    vi.mocked(resolveReport).mockResolvedValue({ ...r, status: 'resolved' })
    const { onClose } = renderModal()
    fireEvent.change(screen.getByTestId('resolve-note'), {
      target: { value: '  치웠음  ' },
    })
    fireEvent.change(screen.getByTestId('resolve-photo-url'), {
      target: { value: 'https://x.com/a.jpg' },
    })
    fireEvent.click(screen.getByTestId('resolve-submit-button'))
    await waitFor(() =>
      expect(resolveReport).toHaveBeenCalledWith('r-1', {
        resolution_note: '치웠음',
        photo_url: 'https://x.com/a.jpg',
      }),
    )
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })

  it('photo URL omitted when blank', async () => {
    vi.mocked(resolveReport).mockResolvedValue({ ...r, status: 'resolved' })
    renderModal()
    fireEvent.change(screen.getByTestId('resolve-note'), {
      target: { value: 'ok' },
    })
    fireEvent.click(screen.getByTestId('resolve-submit-button'))
    await waitFor(() =>
      expect(resolveReport).toHaveBeenCalledWith('r-1', {
        resolution_note: 'ok',
        photo_url: null,
      }),
    )
  })

  it('shows 24h-window error for 403', async () => {
    vi.mocked(resolveReport).mockRejectedValue({
      response: { status: 403, headers: { 'retry-after': '7200' } },
    })
    renderModal()
    fireEvent.change(screen.getByTestId('resolve-note'), {
      target: { value: '치웠음' },
    })
    fireEvent.click(screen.getByTestId('resolve-submit-button'))
    expect(
      await screen.findByText(/24시간 후에 해결 가능/),
    ).toBeInTheDocument()
  })
})
