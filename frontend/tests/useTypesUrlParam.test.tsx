import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useTypesUrlParam } from '@/features/map/useTypesUrlParam'
import { ALL_POI_TYPES } from '@/types/poi'

describe('useTypesUrlParam', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/')
  })
  afterEach(() => {
    window.history.replaceState({}, '', '/')
  })

  it('defaults to all types when no param', () => {
    const { result } = renderHook(() => useTypesUrlParam())
    expect(result.current[0]).toEqual([...ALL_POI_TYPES])
  })

  it('reads ?types=toilet,bench on mount', () => {
    window.history.replaceState({}, '', '/?types=toilet,bench')
    const { result } = renderHook(() => useTypesUrlParam())
    expect(result.current[0]).toEqual(['toilet', 'bench'])
  })

  it('drops unknown values silently', () => {
    window.history.replaceState({}, '', '/?types=toilet,fake_thing,bench')
    const { result } = renderHook(() => useTypesUrlParam())
    expect(result.current[0]).toEqual(['toilet', 'bench'])
  })

  it('?types= (empty) means none active', () => {
    window.history.replaceState({}, '', '/?types=')
    const { result } = renderHook(() => useTypesUrlParam())
    expect(result.current[0]).toEqual([])
  })

  it('setter writes URL with comma-joined value', () => {
    const { result } = renderHook(() => useTypesUrlParam())
    act(() => {
      result.current[1](['toilet', 'bench'])
    })
    expect(new URL(window.location.href).searchParams.get('types')).toBe(
      'toilet,bench',
    )
    expect(result.current[0]).toEqual(['toilet', 'bench'])
  })

  it('setter with all types drops the param (implicit default)', () => {
    window.history.replaceState({}, '', '/?types=toilet')
    const { result } = renderHook(() => useTypesUrlParam())
    act(() => {
      result.current[1]([...ALL_POI_TYPES])
    })
    expect(new URL(window.location.href).searchParams.get('types')).toBeNull()
    expect(result.current[0].sort()).toEqual([...ALL_POI_TYPES].sort())
  })

  it('setter with empty list writes ?types= (explicit none)', () => {
    const { result } = renderHook(() => useTypesUrlParam())
    act(() => {
      result.current[1]([])
    })
    // URLSearchParams stores empty value
    expect(window.location.search).toContain('types=')
    expect(result.current[0]).toEqual([])
  })
})
