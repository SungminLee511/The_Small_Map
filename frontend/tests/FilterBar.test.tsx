import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FilterBar } from '@/features/map/FilterBar'
import { ALL_POI_TYPES } from '@/types/poi'
import type { POIType } from '@/types/poi'

describe('FilterBar', () => {
  it('renders all POI type buttons', () => {
    render(<FilterBar activeTypes={[...ALL_POI_TYPES]} onChange={vi.fn()} />)
    expect(screen.getByText(/화장실/)).toBeInTheDocument()
    expect(screen.getByText(/쓰레기통/)).toBeInTheDocument()
    expect(screen.getByText(/벤치/)).toBeInTheDocument()
    expect(screen.getByText(/흡연구역/)).toBeInTheDocument()
    expect(screen.getByText(/음수대/)).toBeInTheDocument()
  })

  it('calls onChange when toggling a type off', () => {
    const onChange = vi.fn()
    render(<FilterBar activeTypes={[...ALL_POI_TYPES]} onChange={onChange} />)

    fireEvent.click(screen.getByText(/화장실/))
    const called = onChange.mock.calls[0][0] as POIType[]
    expect(called).not.toContain('toilet')
    expect(called).toHaveLength(ALL_POI_TYPES.length - 1)
  })

  it('calls onChange when toggling a type on', () => {
    const onChange = vi.fn()
    render(<FilterBar activeTypes={['bench']} onChange={onChange} />)

    fireEvent.click(screen.getByText(/화장실/))
    const called = onChange.mock.calls[0][0] as POIType[]
    expect(called).toContain('toilet')
    expect(called).toContain('bench')
  })

  it('toggle all button deselects when all selected', () => {
    const onChange = vi.fn()
    render(<FilterBar activeTypes={[...ALL_POI_TYPES]} onChange={onChange} />)

    fireEvent.click(screen.getByText('전체 해제'))
    expect(onChange).toHaveBeenCalledWith([])
  })

  it('toggle all button selects all when none selected', () => {
    const onChange = vi.fn()
    render(<FilterBar activeTypes={[]} onChange={onChange} />)

    fireEvent.click(screen.getByText('전체 선택'))
    expect(onChange).toHaveBeenCalledWith([...ALL_POI_TYPES])
  })
})
