import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Skeleton } from '@/components/Skeleton'

describe('Skeleton', () => {
  it('renders a single block by default', () => {
    render(<Skeleton width={100} height={20} />)
    const el = screen.getByTestId('skeleton')
    expect(el.tagName.toLowerCase()).toBe('div')
    expect(el.style.width).toBe('100px')
    expect(el.style.height).toBe('20px')
  })

  it('renders N rows when rows > 1', () => {
    render(
      <Skeleton width="100%" height={16} rows={3} testId="my-skel" />,
    )
    const wrap = screen.getByTestId('my-skel')
    expect(wrap.children.length).toBe(3)
  })

  it('uses aria-hidden so screen readers skip it', () => {
    render(<Skeleton width={50} height={10} />)
    expect(
      screen.getByTestId('skeleton').getAttribute('aria-hidden'),
    ).toBe('true')
  })
})
