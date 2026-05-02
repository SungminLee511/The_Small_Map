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

  it('"전체" quick toggle selects every type', () => {
    const onChange = vi.fn()
    render(<FilterBar activeTypes={['bench']} onChange={onChange} />)
    fireEvent.click(screen.getByText('전체'))
    expect(onChange).toHaveBeenCalledWith([...ALL_POI_TYPES])
  })

  it('"없음" quick toggle clears every type', () => {
    const onChange = vi.fn()
    render(<FilterBar activeTypes={[...ALL_POI_TYPES]} onChange={onChange} />)
    fireEvent.click(screen.getByText('없음'))
    expect(onChange).toHaveBeenCalledWith([])
  })

  it('"전체" disabled when all selected', () => {
    render(<FilterBar activeTypes={[...ALL_POI_TYPES]} onChange={vi.fn()} />)
    expect((screen.getByText('전체') as HTMLButtonElement).disabled).toBe(true)
  })

  it('"없음" disabled when none selected', () => {
    render(<FilterBar activeTypes={[]} onChange={vi.fn()} />)
    expect((screen.getByText('없음') as HTMLButtonElement).disabled).toBe(true)
  })

  it('aria-pressed reflects active state', () => {
    render(<FilterBar activeTypes={['toilet']} onChange={vi.fn()} />)
    expect(
      screen.getByTestId('filter-toilet').getAttribute('aria-pressed'),
    ).toBe('true')
    expect(
      screen.getByTestId('filter-bench').getAttribute('aria-pressed'),
    ).toBe('false')
  })
})
