import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SubmitSheet } from '@/features/submit/SubmitSheet'

vi.mock('@/api/submit', () => ({
  presignPhoto: vi.fn(),
  uploadPhotoBytes: vi.fn(),
  submitPOI: vi.fn(),
}))

import { submitPOI } from '@/api/submit'

function renderSheet(extra?: Partial<Parameters<typeof SubmitSheet>[0]>) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onClose = vi.fn()
  const onCreated = vi.fn()
  const onDuplicate = vi.fn()
  const utils = render(
    <QueryClientProvider client={qc}>
      <SubmitSheet
        initialLocation={{ lat: 37.55, lng: 126.92 }}
        onClose={onClose}
        onCreated={onCreated}
        onDuplicate={onDuplicate}
        {...extra}
      />
    </QueryClientProvider>,
  )
  return { ...utils, onClose, onCreated, onDuplicate }
}

describe('SubmitSheet', () => {
  beforeEach(() => {
    vi.mocked(submitPOI).mockReset()
  })

  it('opens on the type-picker step', () => {
    renderSheet()
    expect(screen.getByTestId('submit-step-type')).toBeInTheDocument()
    expect(screen.getByText(/새 장소 추가 \(1\/5\)/)).toBeInTheDocument()
  })

  it('next is disabled until a type is picked', () => {
    renderSheet()
    expect((screen.getByTestId('submit-next') as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(screen.getByTestId('submit-type-toilet'))
    expect((screen.getByTestId('submit-next') as HTMLButtonElement).disabled).toBe(false)
  })

  it('advances through type → gps step', () => {
    renderSheet()
    fireEvent.click(screen.getByTestId('submit-type-toilet'))
    fireEvent.click(screen.getByTestId('submit-next'))
    expect(screen.getByTestId('submit-step-gps')).toBeInTheDocument()
  })

  it('close button calls onClose', () => {
    const { onClose } = renderSheet()
    fireEvent.click(screen.getByLabelText('Close submit sheet'))
    expect(onClose).toHaveBeenCalled()
  })
})
