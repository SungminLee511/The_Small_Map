import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReputationGraph } from '@/features/profile/ReputationGraph'
import type { ReputationEvent } from '@/api/me'

function ev(delta: number, iso: string): ReputationEvent {
  return {
    id: `e-${iso}`,
    event_type: 'confirmation',
    delta,
    ref_id: null,
    created_at: iso,
  }
}

describe('ReputationGraph', () => {
  it('renders empty placeholder for zero events', () => {
    render(<ReputationGraph events={[]} />)
    expect(screen.getByTestId('rep-graph-empty')).toBeInTheDocument()
  })

  it('renders an SVG path for >= 1 event', () => {
    render(
      <ReputationGraph
        events={[
          ev(1, '2026-01-01T00:00:00Z'),
          ev(5, '2026-02-01T00:00:00Z'),
          ev(-3, '2026-03-01T00:00:00Z'),
        ]}
      />,
    )
    const svg = screen.getByTestId('rep-graph')
    expect(svg.tagName.toLowerCase()).toBe('svg')
    expect(svg.querySelector('path')).toBeTruthy()
  })

  it('plots one circle per event', () => {
    const events = [
      ev(1, '2026-01-01T00:00:00Z'),
      ev(2, '2026-01-02T00:00:00Z'),
    ]
    render(<ReputationGraph events={events} />)
    expect(
      screen.getByTestId('rep-graph').querySelectorAll('circle').length,
    ).toBe(2)
  })
})
