import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReportSubmitModal } from '@/features/reports/ReportSubmitModal'

vi.mock('@/api/reports', () => ({
  submitReport: vi.fn(),
}))

import { submitReport } from '@/api/reports'

function renderModal(extra?: Partial<Parameters<typeof ReportSubmitModal>[0]>) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onClose = vi.fn()
  const onSubmitted = vi.fn()
  return {
    onClose,
    onSubmitted,
    ...render(
      <QueryClientProvider client={qc}>
        <ReportSubmitModal
          poiId="11111111-1111-1111-1111-111111111111"
          onClose={onClose}
          onSubmitted={onSubmitted}
          {...extra}
        />
      </QueryClientProvider>,
    ),
  }
}

describe('ReportSubmitModal', () => {
  beforeEach(() => {
    vi.mocked(submitReport).mockReset()
  })

  it('renders all 7 report-type buttons', () => {
    renderModal()
    for (const t of [
      'out_of_order',
      'overflowing',
      'dirty',
      'closed',
      'damaged',
      'vandalized',
      'other',
    ]) {
      expect(screen.getByTestId(`report-type-${t}`)).toBeInTheDocument()
    }
  })

  it('submit disabled until a type is picked', () => {
    renderModal()
    const btn = screen.getByTestId('report-submit-button') as HTMLButtonElement
    expect(btn.disabled).toBe(true)
    fireEvent.click(screen.getByTestId('report-type-dirty'))
    expect(btn.disabled).toBe(false)
  })

  it('calls submitReport with chosen type and trimmed description', async () => {
    vi.mocked(submitReport).mockResolvedValue({
      id: 'r-1',
      poi_id: '11111111-1111-1111-1111-111111111111',
      reporter_id: 'u-1',
      report_type: 'dirty',
      description: 'gross',
      photo_url: null,
      status: 'active',
      confirmation_count: 0,
      resolved_at: null,
      resolved_by: null,
      resolution_note: null,
      expires_at: '2026-05-09T00:00:00Z',
      created_at: '2026-05-02T00:00:00Z',
      updated_at: '2026-05-02T00:00:00Z',
    })
    const { onSubmitted, onClose } = renderModal()

    fireEvent.click(screen.getByTestId('report-type-dirty'))
    fireEvent.change(screen.getByTestId('report-description'), {
      target: { value: '  gross  ' },
    })
    fireEvent.click(screen.getByTestId('report-submit-button'))

    await waitFor(() => expect(submitReport).toHaveBeenCalled())
    expect(submitReport).toHaveBeenCalledWith(
      '11111111-1111-1111-1111-111111111111',
      { report_type: 'dirty', description: 'gross' },
    )
    await waitFor(() => expect(onSubmitted).toHaveBeenCalledWith('r-1'))
    expect(onClose).toHaveBeenCalled()
  })

  it('close button fires onClose', () => {
    const { onClose } = renderModal()
    fireEvent.click(screen.getByLabelText('Close report modal'))
    expect(onClose).toHaveBeenCalled()
  })
})
