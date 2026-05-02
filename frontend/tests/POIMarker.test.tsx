import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { POIMarker } from '@/features/map/POIMarker'
import type { POI } from '@/types/poi'

vi.mock('react-kakao-maps-sdk', () => ({
  CustomOverlayMap: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}))

import { vi } from 'vitest'

const basePoi = (overrides?: Partial<POI>): POI => ({
  id: '11111111-1111-1111-1111-111111111111',
  poi_type: 'toilet',
  location: { lat: 37.5, lng: 126.9 },
  name: 'Test',
  attributes: {},
  source: 'seed',
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
  ...overrides,
})

describe('POIMarker', () => {
  it('marks verified POIs without unverified badge', () => {
    const { container } = render(
      <POIMarker poi={basePoi({ verification_status: 'verified' })} />,
    )
    const btn = container.querySelector('[data-testid="poi-marker"]')
    expect(btn?.getAttribute('data-verification-status')).toBe('verified')
    expect(container.textContent).not.toContain('?')
  })

  it('renders unverified ring + ? badge for user submissions', () => {
    const { container } = render(
      <POIMarker poi={basePoi({ verification_status: 'unverified' })} />,
    )
    const btn = container.querySelector('[data-testid="poi-marker"]')
    expect(btn?.getAttribute('data-verification-status')).toBe('unverified')
    expect(container.textContent).toContain('?')
  })

  it('default (missing field) treated as verified', () => {
    const { container } = render(<POIMarker poi={basePoi()} />)
    const btn = container.querySelector('[data-testid="poi-marker"]')
    expect(btn?.getAttribute('data-verification-status')).toBe('verified')
  })
})
