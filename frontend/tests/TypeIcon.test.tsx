import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import {
  POI_TYPE_COLORS,
  POI_TYPE_LUCIDE,
  TypeIcon,
} from '@/features/map/TypeIcon'
import { ALL_POI_TYPES } from '@/types/poi'

describe('POI_TYPE_LUCIDE', () => {
  it('has one icon per POI type', () => {
    for (const t of ALL_POI_TYPES) {
      expect(POI_TYPE_LUCIDE[t]).toBeTruthy()
    }
  })

  it('all icons are distinct', () => {
    const set = new Set(ALL_POI_TYPES.map((t) => POI_TYPE_LUCIDE[t]))
    expect(set.size).toBe(ALL_POI_TYPES.length)
  })

  it('has one color per POI type', () => {
    for (const t of ALL_POI_TYPES) {
      expect(POI_TYPE_COLORS[t]).toMatch(/^#[0-9a-f]{6}$/i)
    }
  })

  it('colors are distinct', () => {
    const set = new Set(ALL_POI_TYPES.map((t) => POI_TYPE_COLORS[t]))
    expect(set.size).toBe(ALL_POI_TYPES.length)
  })
})

describe('TypeIcon', () => {
  it('renders an svg element', () => {
    const { container } = render(<TypeIcon poi_type="toilet" />)
    expect(container.querySelector('svg')).toBeTruthy()
  })

  it('uses the type color in default mode', () => {
    const { container } = render(<TypeIcon poi_type="toilet" />)
    const span = container.querySelector('span')
    expect(span?.getAttribute('style')).toContain(POI_TYPE_COLORS.toilet)
  })

  it('bare mode does not wrap in colored circle', () => {
    const { container } = render(<TypeIcon poi_type="bench" bare />)
    expect(container.querySelector('span')).toBeNull()
    expect(container.querySelector('svg')).toBeTruthy()
  })
})
