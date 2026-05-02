import { CustomOverlayMap } from 'react-kakao-maps-sdk'
import type { POIType } from '@/types/poi'

interface ClusterMarkerProps {
  lat: number
  lng: number
  count: number
  dominantType: POIType | null
  onClick?: () => void
}

/** Color per dominant type. Mixed (null) = neutral gray. */
const TYPE_COLORS: Record<POIType, string> = {
  toilet: '#3b82f6',
  trash_can: '#10b981',
  bench: '#f59e0b',
  smoking_area: '#6b7280',
  water_fountain: '#06b6d4',
}

/** Circle size scales loosely with count. */
function sizeFor(count: number): number {
  if (count < 10) return 36
  if (count < 100) return 44
  if (count < 1000) return 52
  return 60
}

export function ClusterMarker({
  lat,
  lng,
  count,
  dominantType,
  onClick,
}: ClusterMarkerProps) {
  const bg = dominantType ? TYPE_COLORS[dominantType] : '#9ca3af'
  const size = sizeFor(count)

  return (
    <CustomOverlayMap position={{ lat, lng }} yAnchor={0.5} xAnchor={0.5}>
      <button
        type="button"
        onClick={onClick}
        aria-label={`${count} POIs clustered here`}
        data-testid="cluster-marker"
        style={{
          width: size,
          height: size,
          backgroundColor: bg,
        }}
        className="rounded-full text-white font-bold shadow-lg border-2 border-white flex items-center justify-center text-sm cursor-pointer hover:scale-110 transition"
      >
        {count >= 1000 ? `${(count / 1000).toFixed(1)}k` : count}
      </button>
    </CustomOverlayMap>
  )
}
