import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchPOI } from '@/api/pois'
import { POI_TYPE_ICONS, POI_TYPE_LABELS } from '@/types/poi'
import type { POIDetail, POIType } from '@/types/poi'

interface POIDetailPanelProps {
  poiId: string | null
  onClose: () => void
}

/**
 * Right-rail (desktop) / bottom-sheet (mobile) panel showing full POI detail.
 * Fetches /pois/{id} on demand, with Esc-to-close and a visible close button.
 * Also surfaces source attribution per KOGL Type 1 license.
 */
export function POIDetailPanel({ poiId, onClose }: POIDetailPanelProps) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['poi', poiId],
    queryFn: () => fetchPOI(poiId as string),
    enabled: !!poiId,
    staleTime: 60_000,
    retry: 0,
  })

  // Esc to close
  useEffect(() => {
    if (!poiId) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [poiId, onClose])

  if (!poiId) return null

  return (
    <aside
      role="dialog"
      aria-modal="false"
      aria-label="POI detail"
      data-testid="poi-detail-panel"
      className="fixed bottom-0 left-0 right-0 md:top-0 md:bottom-0 md:left-auto md:right-0 md:w-96 z-20 bg-white shadow-xl border-t md:border-t-0 md:border-l border-gray-200 max-h-[70vh] md:max-h-screen overflow-y-auto"
    >
      <header className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">POI 상세</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close detail panel"
          className="text-gray-500 hover:text-gray-900 text-xl leading-none px-2"
        >
          ×
        </button>
      </header>

      <div className="px-4 py-3">
        {isLoading && <p className="text-gray-500">로딩 중…</p>}
        {isError && (
          <p className="text-red-500" role="alert">
            불러오기 실패: {(error as Error)?.message ?? 'unknown'}
          </p>
        )}
        {data && <POIBody poi={data} />}
      </div>
    </aside>
  )
}

function POIBody({ poi }: { poi: POIDetail }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-3xl" aria-hidden="true">
          {POI_TYPE_ICONS[poi.poi_type]}
        </span>
        <div>
          <h3 className="text-xl font-bold">
            {poi.name ?? POI_TYPE_LABELS[poi.poi_type]}
          </h3>
          <p className="text-sm text-gray-500">{POI_TYPE_LABELS[poi.poi_type]}</p>
        </div>
      </div>

      <Attributes poi_type={poi.poi_type} attrs={poi.attributes ?? {}} />

      <dl className="text-sm text-gray-700 space-y-1 pt-2 border-t border-gray-100">
        {poi.last_verified_at && (
          <div className="flex justify-between">
            <dt className="text-gray-500">최근 확인</dt>
            <dd>{formatDate(poi.last_verified_at)}</dd>
          </div>
        )}
        <div className="flex justify-between">
          <dt className="text-gray-500">확인 수</dt>
          <dd>{poi.verification_count}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-gray-500">출처</dt>
          <dd className="text-right">{sourceLabel(poi.source)}</dd>
        </div>
      </dl>
    </div>
  )
}

function Attributes({
  poi_type,
  attrs,
}: {
  poi_type: POIType
  attrs: Record<string, unknown>
}) {
  const lines = formatAttributes(poi_type, attrs)
  if (lines.length === 0) {
    return <p className="text-sm text-gray-500">상세 정보 없음</p>
  }
  return (
    <ul className="flex flex-wrap gap-2 text-sm">
      {lines.map((line, i) => (
        <li
          key={i}
          className="bg-gray-100 rounded-full px-3 py-1 text-gray-700"
        >
          {line}
        </li>
      ))}
    </ul>
  )
}

export function formatAttributes(
  poi_type: POIType,
  a: Record<string, unknown>,
): string[] {
  const lines: string[] = []
  switch (poi_type) {
    case 'toilet':
      if (a.accessibility === true) lines.push('♿ 장애인용')
      if (a.gender === 'separate') lines.push('남녀 분리')
      else if (a.gender === 'unisex') lines.push('남녀 공용')
      else if (a.gender === 'male_only') lines.push('남성 전용')
      else if (a.gender === 'female_only') lines.push('여성 전용')
      if (a.is_free === true) lines.push('무료')
      else if (a.is_free === false) lines.push('유료')
      if (a.has_baby_changing === true) lines.push('기저귀 교환대')
      if (typeof a.opening_hours === 'string' && a.opening_hours)
        lines.push(`🕐 ${a.opening_hours}`)
      break
    case 'trash_can':
      if (a.recycling === true) lines.push('재활용')
      if (a.general === true) lines.push('일반')
      break
    case 'bench':
      if (typeof a.material === 'string' && a.material) lines.push(a.material)
      if (a.has_back === true) lines.push('등받이 있음')
      if (a.shaded === true) lines.push('그늘 있음')
      break
    case 'smoking_area':
      if (a.enclosed === true) lines.push('실내/폐쇄형')
      else if (a.enclosed === false) lines.push('야외/개방형')
      if (typeof a.opening_hours === 'string' && a.opening_hours)
        lines.push(`🕐 ${a.opening_hours}`)
      break
    case 'water_fountain':
      if (a.is_potable === true) lines.push('음용 가능')
      if (a.seasonal === true) lines.push('계절제')
      break
  }
  return lines
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('ko-KR')
  } catch {
    return iso
  }
}

function sourceLabel(source: string): string {
  if (source === 'seoul.public_toilets')
    return '공공데이터포털 (data.go.kr) — 전국공중화장실표준데이터'
  if (source === 'mapo.smoking_areas')
    return '공공데이터포털 (data.go.kr) — 마포구 흡연시설 현황'
  if (source === 'seed') return '시드 데이터'
  if (source.startsWith('user:')) return '사용자 등록'
  return source
}
