import { useState, useCallback, useRef } from 'react'
import { Map, useKakaoLoader } from 'react-kakao-maps-sdk'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchPOIs } from '@/api/pois'
import { AuthHeader } from '@/features/auth/AuthHeader'
import { useMe } from '@/features/auth/useMe'
import { Footer } from '@/features/static/Footer'
import { SubmitSheet } from '@/features/submit/SubmitSheet'
import { Plus } from 'lucide-react'
import { FilterBar } from './FilterBar'
import { ClusterMarker } from './ClusterMarker'
import { POIDetailPanel } from './POIDetailPanel'
import { POIMarker } from './POIMarker'
import { useClusters } from './useClusters'
import { usePoiUrlParam } from './usePoiUrlParam'
import { useTypesUrlParam } from './useTypesUrlParam'
import { ALL_POI_TYPES } from '@/types/poi'
import type { BBox } from '@/types/poi'

// Mapo-gu center
const DEFAULT_CENTER = { lat: 37.5535, lng: 126.9215 }
const DEFAULT_LEVEL = 5

export function MapView() {
  const [loading, error] = useKakaoLoader({
    appkey: import.meta.env.VITE_KAKAO_MAPS_JS_KEY || '',
  })

  const [activeTypes, setActiveTypes] = useTypesUrlParam()
  const [bbox, setBbox] = useState<BBox | null>(null)
  const [level, setLevel] = useState<number>(DEFAULT_LEVEL)
  const [selectedPoiId, setSelectedPoiId] = usePoiUrlParam()
  const [submitOpen, setSubmitOpen] = useState(false)
  const [center, setCenter] = useState(DEFAULT_CENTER)
  const mapRef = useRef<kakao.maps.Map | null>(null)
  const { data: me } = useMe()
  const queryClient = useQueryClient()

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
    const c = map.getCenter()
    setCenter({ lat: c.getLat(), lng: c.getLng() })
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
      <AuthHeader />
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
            <POIMarker
              key={c.poi.id}
              poi={c.poi}
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
      <Footer />
      <POIDetailPanel
        poiId={selectedPoiId}
        onClose={() => setSelectedPoiId(null)}
      />
      {me && !submitOpen && (
        <button
          type="button"
          onClick={() => setSubmitOpen(true)}
          aria-label="Add a new POI"
          data-testid="submit-fab"
          className="fixed bottom-6 right-6 z-20 bg-blue-600 hover:bg-blue-700 text-white rounded-full w-14 h-14 shadow-xl flex items-center justify-center"
        >
          <Plus size={28} aria-hidden="true" />
        </button>
      )}
      {submitOpen && (
        <SubmitSheet
          initialLocation={center}
          onClose={() => setSubmitOpen(false)}
          onCreated={(poiId) => {
            setSubmitOpen(false)
            // Refetch the bbox query so the new pin appears
            queryClient.invalidateQueries({ queryKey: ['pois'] })
            setSelectedPoiId(poiId)
          }}
          onDuplicate={(dup) => {
            setSubmitOpen(false)
            setSelectedPoiId(dup.existing_poi_id)
          }}
        />
      )}
    </div>
  )
}
