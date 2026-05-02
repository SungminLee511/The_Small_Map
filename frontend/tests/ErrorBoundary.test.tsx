import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorBoundary } from '@/components/ErrorBoundary'

function Boom({ when }: { when: boolean }) {
  if (when) throw new Error('boom!')
  return <span data-testid="ok">ok</span>
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  it('renders children when nothing throws', () => {
    render(
      <ErrorBoundary>
        <Boom when={false} />
      </ErrorBoundary>,
    )
    expect(screen.getByTestId('ok')).toBeInTheDocument()
  })

  it('renders default fallback on throw and shows message', () => {
    render(
      <ErrorBoundary>
        <Boom when />
      </ErrorBoundary>,
    )
    expect(screen.getByTestId('error-boundary')).toBeInTheDocument()
    expect(screen.getByText(/boom/)).toBeInTheDocument()
  })

  it('reset button clears the error', () => {
    let throwIt = true
    function Maybe() {
      if (throwIt) throw new Error('first')
      return <span data-testid="recovered">recovered</span>
    }
    const { rerender } = render(
      <ErrorBoundary>
        <Maybe />
      </ErrorBoundary>,
    )
    throwIt = false
    fireEvent.click(screen.getByText('다시 시도'))
    rerender(
      <ErrorBoundary>
        <Maybe />
      </ErrorBoundary>,
    )
    expect(screen.getByTestId('recovered')).toBeInTheDocument()
  })

  it('uses custom fallback when supplied', () => {
    render(
      <ErrorBoundary
        fallback={(err) => (
          <div data-testid="custom">custom: {err.message}</div>
        )}
      >
        <Boom when />
      </ErrorBoundary>,
    )
    expect(screen.getByTestId('custom').textContent).toBe('custom: boom!')
  })
})
