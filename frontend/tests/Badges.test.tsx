import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badges } from '@/features/profile/Badges'
import type { POIDetail } from '@/types/poi'

const me = {
  id: 'me-1',
  display_name: 'M',
  email: null,
  avatar_url: null,
  is_admin: false,
  reputation: 0,
}

const sub: POIDetail = {
  id: 'p',
  poi_type: 'toilet',
  location: { lat: 0, lng: 0 },
  name: null,
  attributes: {},
  source: 'user:me-1',
  status: 'active',
  verification_status: 'verified',
  external_id: null,
  last_verified_at: null,
  verification_count: 1,
  created_at: '',
  updated_at: '',
}

describe('Badges', () => {
  it('Trusted badge unearned at rep 49', () => {
    render(<Badges me={{ ...me, reputation: 49 }} submissions={[]} confirmations={[]} />)
    expect(
      screen.getByTestId('badge-trusted').getAttribute('data-earned'),
    ).toBe('false')
  })

  it('Trusted badge earned at rep 50', () => {
    render(<Badges me={{ ...me, reputation: 50 }} submissions={[]} confirmations={[]} />)
    expect(
      screen.getByTestId('badge-trusted').getAttribute('data-earned'),
    ).toBe('true')
  })

  it('First-submission badge earned with at least one submission', () => {
    render(<Badges me={me} submissions={[sub]} confirmations={[]} />)
    expect(
      screen.getByTestId('badge-first-submission').getAttribute('data-earned'),
    ).toBe('true')
  })

  it('Confirmer badge needs >= 10 confirmations', () => {
    const nine = Array.from({ length: 9 }, () => sub)
    const ten = Array.from({ length: 10 }, () => sub)
    const { rerender } = render(
      <Badges me={me} submissions={[]} confirmations={nine} />,
    )
    expect(
      screen.getByTestId('badge-confirmer').getAttribute('data-earned'),
    ).toBe('false')
    rerender(<Badges me={me} submissions={[]} confirmations={ten} />)
    expect(
      screen.getByTestId('badge-confirmer').getAttribute('data-earned'),
    ).toBe('true')
  })
})
