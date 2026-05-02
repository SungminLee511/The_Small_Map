import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { POIMarker } from '@/features/map/POIMarker'
import type { POI } from '@/types/poi'

vi.mock('react-kakao-maps-sdk', () => ({
  CustomOverlayMap: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}))

const base: POI = {
  id: '11111111-1111-1111-1111-111111111111',
  poi_type: 'toilet',
  location: { lat: 37.5, lng: 126.9 },
  name: 'T',
  attributes: {},
  source: 'seed',
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('POIMarker — report badge', () => {
  it('hides the badge when active_report_count is missing or zero', () => {
    const { queryByTestId } = render(<POIMarker poi={base} />)
    expect(queryByTestId('poi-report-badge')).toBeNull()
  })

  it('shows red badge with count when active_report_count > 0', () => {
    const { getByTestId } = render(
      <POIMarker poi={{ ...base, active_report_count: 3 }} />,
    )
    const badge = getByTestId('poi-report-badge')
    expect(badge).toBeInTheDocument()
    expect(badge.textContent).toBe('3')
  })

  it('caps display at 9+ for big numbers', () => {
    const { getByTestId } = render(
      <POIMarker poi={{ ...base, active_report_count: 42 }} />,
    )
    expect(getByTestId('poi-report-badge').textContent).toBe('9+')
  })

  it('exposes the count via data attribute for e2e selectors', () => {
    const { container } = render(
      <POIMarker poi={{ ...base, active_report_count: 2 }} />,
    )
    const btn = container.querySelector('[data-testid="poi-marker"]')
    expect(btn?.getAttribute('data-active-report-count')).toBe('2')
  })
})
