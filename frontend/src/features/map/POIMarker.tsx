import { CustomOverlayMap } from 'react-kakao-maps-sdk'
import { TypeIcon } from './TypeIcon'
import type { POI } from '@/types/poi'

interface POIMarkerProps {
  poi: POI
  onClick?: () => void
}

/**
 * Custom POI marker: colored circle + Lucide icon, click → detail.
 *
 * Unverified user submissions get a dashed outline + "?" badge so the
 * map clearly distinguishes them from imported / verified entries.
 */
export function POIMarker({ poi, onClick }: POIMarkerProps) {
  const isUnverified = poi.verification_status === 'unverified'
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
        data-verification-status={poi.verification_status ?? 'verified'}
        className={`relative cursor-pointer hover:scale-110 transition ${
          isUnverified ? 'opacity-80' : ''
        }`}
      >
        <span
          className={`block rounded-full ${
            isUnverified
              ? 'ring-2 ring-yellow-500 ring-dashed p-0.5'
              : ''
          }`}
        >
          <TypeIcon poi_type={poi.poi_type} size={32} />
        </span>
        {isUnverified && (
          <span
            aria-hidden="true"
            className="absolute -top-1 -right-1 bg-yellow-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center border border-white"
          >
            ?
          </span>
        )}
      </button>
    </CustomOverlayMap>
  )
}
