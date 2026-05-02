import React from 'react'

interface ErrorBoundaryState {
  err: Error | null
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: (err: Error, reset: () => void) => React.ReactNode
}

/**
 * Top-level error boundary (Phase 4.3.5).
 *
 * React boundaries can't be functional. We keep this dependency-free —
 * it logs to console.error for now; a future commit can wire Sentry.
 */
export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { err: null }

  static getDerivedStateFromError(err: Error): ErrorBoundaryState {
    return { err }
  }

  componentDidCatch(err: Error, info: React.ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', err, info)
  }

  reset = () => this.setState({ err: null })

  render() {
    if (this.state.err) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.err, this.reset)
      }
      return <DefaultFallback err={this.state.err} reset={this.reset} />
    }
    return this.props.children
  }
}

function DefaultFallback({
  err,
  reset,
}: {
  err: Error
  reset: () => void
}) {
  return (
    <main
      role="alert"
      data-testid="error-boundary"
      className="flex flex-col items-center justify-center min-h-screen px-4 text-center"
    >
      <div className="max-w-md">
        <p className="text-4xl mb-2" aria-hidden="true">
          ⚠️
        </p>
        <h1 className="text-xl font-bold mb-2">잠시 문제가 발생했어요</h1>
        <p className="text-sm text-gray-600 mb-4 break-words">
          {err.message || 'Unknown error'}
        </p>
        <div className="flex gap-2 justify-center">
          <button
            type="button"
            onClick={reset}
            className="px-3 py-1.5 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm font-semibold"
          >
            다시 시도
          </button>
          <a
            href="/"
            className="px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-800 text-sm font-semibold"
          >
            지도로
          </a>
        </div>
      </div>
    </main>
  )
}
