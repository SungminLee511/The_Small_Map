import { useMemo } from 'react'
import type { ReputationEvent } from '@/api/me'

interface ReputationGraphProps {
  events: ReputationEvent[]
  /** Width of the SVG in px. Height is scaled. */
  width?: number
}

/**
 * Tiny SVG line chart of cumulative reputation over time (Phase 4.3.2).
 * No external chart lib — keeps the bundle small and CI-friendly.
 *
 * Empty events → empty placeholder.
 */
export function ReputationGraph({ events, width = 280 }: ReputationGraphProps) {
  const series = useMemo(() => buildSeries(events), [events])

  if (series.length === 0) {
    return (
      <p className="text-xs text-gray-500" data-testid="rep-graph-empty">
        평판 이력이 없습니다.
      </p>
    )
  }

  const height = 80
  const padX = 4
  const padY = 6
  const xs = series.map((p) => p.t)
  const ys = series.map((p) => p.rep)
  const xMin = Math.min(...xs)
  const xMax = Math.max(...xs)
  const yMin = Math.min(...ys, 0)
  const yMax = Math.max(...ys, 1)
  const xRange = xMax - xMin || 1
  const yRange = yMax - yMin || 1

  const points = series.map((p) => {
    const x = padX + ((p.t - xMin) / xRange) * (width - 2 * padX)
    const y =
      height - padY - ((p.rep - yMin) / yRange) * (height - 2 * padY)
    return [x, y] as const
  })
  const path = points
    .map(([x, y], i) => `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`)
    .join(' ')

  return (
    <svg
      role="img"
      aria-label="평판 이력"
      data-testid="rep-graph"
      width={width}
      height={height}
      className="block"
    >
      <line
        x1={padX}
        y1={height - padY}
        x2={width - padX}
        y2={height - padY}
        stroke="#e5e7eb"
      />
      <path
        d={path}
        fill="none"
        stroke="#3b82f6"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {points.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={2.5} fill="#3b82f6" />
      ))}
    </svg>
  )
}

function buildSeries(
  events: ReputationEvent[],
): { t: number; rep: number }[] {
  if (events.length === 0) return []
  const sorted = [...events].sort(
    (a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  )
  let acc = 0
  return sorted.map((e) => {
    acc += e.delta
    return { t: new Date(e.created_at).getTime(), rep: acc }
  })
}
