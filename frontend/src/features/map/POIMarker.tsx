import { CustomOverlayMap } from 'react-kakao-maps-sdk'
import { TypeIcon } from './TypeIcon'
import type { POI } from '@/types/poi'

interface POIMarkerProps {
  poi: POI
  onClick?: () => void
}

/** Custom POI marker: colored circle + Lucide icon, click → detail. */
export function POIMarker({ poi, onClick }: POIMarkerProps) {
  return (
    <CustomOverlayMap
      position={{ lat: poi.location.lat, lng: poi.location.lng }}
      yAnchor={0.5}
      xAnchor={0.5}
    >
      <button
        type="button"
        onClick={onClick}
        title={poi.name ?? undefined}
        aria-label={poi.name ?? poi.poi_type}
        data-testid="poi-marker"
        data-poi-id={poi.id}
        data-poi-type={poi.poi_type}
        className="cursor-pointer hover:scale-110 transition"
      >
        <TypeIcon poi_type={poi.poi_type} size={32} />
      </button>
    </CustomOverlayMap>
  )
}
