import { useState, useCallback, useRef } from 'react'
import { Map, MapMarker, useKakaoLoader } from 'react-kakao-maps-sdk'
import { useQuery } from '@tanstack/react-query'
import { fetchPOIs } from '@/api/pois'
import { FilterBar } from './FilterBar'
import { ClusterMarker } from './ClusterMarker'
import { POIDetailPanel } from './POIDetailPanel'
import { useClusters } from './useClusters'
import { usePoiUrlParam } from './usePoiUrlParam'
import { ALL_POI_TYPES, POI_TYPE_ICONS } from '@/types/poi'
import type { POIType, BBox } from '@/types/poi'

// Mapo-gu center
const DEFAULT_CENTER = { lat: 37.5535, lng: 126.9215 }
const DEFAULT_LEVEL = 5

export function MapView() {
  const [loading, error] = useKakaoLoader({
    appkey: import.meta.env.VITE_KAKAO_MAPS_JS_KEY || '',
  })

  const [activeTypes, setActiveTypes] = useState<POIType[]>([...ALL_POI_TYPES])
  const [bbox, setBbox] = useState<BBox | null>(null)
  const [level, setLevel] = useState<number>(DEFAULT_LEVEL)
  const [selectedPoiId, setSelectedPoiId] = usePoiUrlParam()
  const mapRef = useRef<kakao.maps.Map | null>(null)

  const updateBboxAndLevel = useCallback(() => {
    const map = mapRef.current
    if (!map) return
    const bounds = map.getBounds()
    const sw = bounds.getSouthWest()
    const ne = bounds.getNorthEast()
    setBbox({
      west: sw.getLng(),
      south: sw.getLat(),
      east: ne.getLng(),
      north: ne.getLat(),
    })
    setLevel(map.getLevel())
  }, [])

  const { data } = useQuery({
    queryKey: ['pois', bbox, activeTypes],
    queryFn: () =>
      fetchPOIs(
        bbox!,
        activeTypes.length === ALL_POI_TYPES.length ? undefined : activeTypes,
      ),
    enabled: !!bbox && activeTypes.length > 0,
    staleTime: 60_000,
  })

  const clusters = useClusters({ pois: data?.items, bbox, level })

  const onClusterClick = useCallback(
    (lat: number, lng: number) => {
      const map = mapRef.current
      if (!map) return
      // Zoom in by 2 levels (Kakao: smaller = more zoomed) and recenter
      map.setLevel(Math.max(1, map.getLevel() - 2))
      map.setCenter(new kakao.maps.LatLng(lat, lng))
    },
    [],
  )

  if (loading)
    return <div className="flex items-center justify-center h-screen">Loading map...</div>
  if (error)
    return (
      <div className="flex items-center justify-center h-screen text-red-500">
        Map load error
      </div>
    )

  return (
    <div className="relative w-full h-screen">
      <FilterBar activeTypes={activeTypes} onChange={setActiveTypes} />
      <Map
        center={DEFAULT_CENTER}
        level={DEFAULT_LEVEL}
        className="w-full h-full"
        onCreate={(map) => {
          mapRef.current = map
          updateBboxAndLevel()
        }}
        onIdle={updateBboxAndLevel}
      >
        {clusters.map((c) =>
          c.kind === 'cluster' ? (
            <ClusterMarker
              key={`cl-${c.id}`}
              lat={c.lat}
              lng={c.lng}
              count={c.count}
              dominantType={c.dominantType}
              onClick={() => onClusterClick(c.lat, c.lng)}
            />
          ) : (
            <MapMarker
              key={c.poi.id}
              position={{ lat: c.lat, lng: c.lng }}
              title={c.poi.name || POI_TYPE_ICONS[c.poi.poi_type]}
              onClick={() => setSelectedPoiId(c.poi.id)}
            />
          ),
        )}
      </Map>
      {data?.truncated && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-yellow-100 text-yellow-800 px-4 py-2 rounded-lg shadow text-sm">
          Too many results. Zoom in for more detail.
        </div>
      )}
      <POIDetailPanel
        poiId={selectedPoiId}
        onClose={() => setSelectedPoiId(null)}
      />
    </div>
  )
}
