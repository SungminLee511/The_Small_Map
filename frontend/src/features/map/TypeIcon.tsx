import { Toilet, Trash2, Armchair, Cigarette, Droplets } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { POIType } from '@/types/poi'

/**
 * One Lucide icon per POI type, plus a brand color used by markers and
 * the cluster-circle palette. Visually distinct enough to read at a glance.
 */
export const POI_TYPE_LUCIDE: Record<POIType, LucideIcon> = {
  toilet: Toilet,
  trash_can: Trash2,
  bench: Armchair,
  smoking_area: Cigarette,
  water_fountain: Droplets,
}

export const POI_TYPE_COLORS: Record<POIType, string> = {
  toilet: '#3b82f6',       // blue
  trash_can: '#10b981',    // green
  bench: '#f59e0b',        // amber
  smoking_area: '#6b7280', // gray
  water_fountain: '#06b6d4', // cyan
}

interface TypeIconProps {
  poi_type: POIType
  size?: number
  className?: string
  /** When true, renders just the SVG with default fg color (inherits) */
  bare?: boolean
}

/**
 * Default render: a colored circle with the icon centered. Used as a marker.
 * Set ``bare`` to render the icon alone (e.g. inline in text).
 */
export function TypeIcon({ poi_type, size = 32, className, bare }: TypeIconProps) {
  const Icon = POI_TYPE_LUCIDE[poi_type]
  if (bare) {
    return <Icon size={size} className={className} aria-hidden="true" />
  }
  const color = POI_TYPE_COLORS[poi_type]
  return (
    <span
      className={`inline-flex items-center justify-center rounded-full shadow border-2 border-white ${className ?? ''}`}
      style={{ width: size, height: size, backgroundColor: color }}
      aria-hidden="true"
    >
      <Icon size={Math.round(size * 0.55)} color="white" strokeWidth={2.5} />
    </span>
  )
}
