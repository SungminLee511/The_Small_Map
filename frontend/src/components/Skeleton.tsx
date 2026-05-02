interface SkeletonProps {
  className?: string
  width?: string | number
  height?: string | number
  /** Repeat the same row N times, useful for list skeletons. */
  rows?: number
  testId?: string
}

/** Pulsing grey block (Phase 4.3.5). Pure CSS — no `prefers-reduced-motion`
 *  guard since Tailwind's `animate-pulse` is mild. */
export function Skeleton({
  className = '',
  width,
  height,
  rows = 1,
  testId = 'skeleton',
}: SkeletonProps) {
  const style: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  }
  if (rows <= 1) {
    return (
      <div
        data-testid={testId}
        aria-hidden="true"
        className={`bg-gray-200 rounded animate-pulse ${className}`}
        style={style}
      />
    )
  }
  return (
    <div
      data-testid={testId}
      aria-hidden="true"
      className="space-y-2"
    >
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className={`bg-gray-200 rounded animate-pulse ${className}`}
          style={style}
        />
      ))}
    </div>
  )
}
