import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePoiUrlParam } from '@/features/map/usePoiUrlParam'

describe('usePoiUrlParam', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/')
  })
  afterEach(() => {
    window.history.replaceState({}, '', '/')
  })

  it('returns null when no param', () => {
    const { result } = renderHook(() => usePoiUrlParam())
    expect(result.current[0]).toBeNull()
  })

  it('reads existing ?poi= param on mount', () => {
    window.history.replaceState({}, '', '/?poi=abc')
    const { result } = renderHook(() => usePoiUrlParam())
    expect(result.current[0]).toBe('abc')
  })

  it('setter updates URL and state', () => {
    const { result } = renderHook(() => usePoiUrlParam())
    act(() => {
      result.current[1]('xyz')
    })
    expect(result.current[0]).toBe('xyz')
    expect(new URL(window.location.href).searchParams.get('poi')).toBe('xyz')
  })

  it('setter with null removes param', () => {
    window.history.replaceState({}, '', '/?poi=abc')
    const { result } = renderHook(() => usePoiUrlParam())
    expect(result.current[0]).toBe('abc')
    act(() => {
      result.current[1](null)
    })
    expect(result.current[0]).toBeNull()
    expect(new URL(window.location.href).searchParams.get('poi')).toBeNull()
  })
})
