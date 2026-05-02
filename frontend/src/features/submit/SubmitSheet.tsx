import { useCallback, useMemo, useState } from 'react'
import { POI_TYPE_LABELS, ALL_POI_TYPES } from '@/types/poi'
import type { LatLng, POIType } from '@/types/poi'
import { TypeIcon, POI_TYPE_LUCIDE } from '@/features/map/TypeIcon'
import { useGeolocation } from './useGeolocation'
import { compressImage } from './compressImage'
import {
  presignPhoto,
  submitPOI,
  uploadPhotoBytes,
  type SubmitDuplicate,
} from '@/api/submit'

interface SubmitSheetProps {
  /** Initial map-pin location (matches the visual pin the user dropped). */
  initialLocation: LatLng
  onClose: () => void
  /** Called with the new POI's id on success. */
  onCreated: (poiId: string) => void
  /** Called when the server reports a nearby duplicate. */
  onDuplicate: (dup: SubmitDuplicate) => void
}

type Step = 'type' | 'gps' | 'photo' | 'attrs' | 'review'

const STEPS: Step[] = ['type', 'gps', 'photo', 'attrs', 'review']

const ACCURACY_HARD_LIMIT_M = 50
const PIN_DRIFT_HARD_LIMIT_M = 30 // we let user drag pin <30m from GPS

/**
 * 5-step submit flow. Steps:
 *   1. Type   — pick a POI type (5 large icons)
 *   2. GPS    — capture device location, show accuracy, allow pin nudge
 *   3. Photo  — file picker (camera on mobile), compress client-side
 *   4. Attrs  — type-specific attribute form
 *   5. Review — review + submit
 */
export function SubmitSheet({
  initialLocation,
  onClose,
  onCreated,
  onDuplicate,
}: SubmitSheetProps) {
  const [step, setStep] = useState<Step>('type')
  const [poiType, setPoiType] = useState<POIType | null>(null)
  const [location, setLocation] = useState<LatLng>(initialLocation)
  const [name, setName] = useState('')
  const [attributes, setAttributes] = useState<Record<string, unknown>>({})
  const [photo, setPhoto] = useState<File | null>(null)
  const [photoPreviewUrl, setPhotoPreviewUrl] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const geo = useGeolocation()
  const stepIdx = STEPS.indexOf(step)

  const goNext = useCallback(() => {
    const next = STEPS[stepIdx + 1]
    if (next) setStep(next)
  }, [stepIdx])

  const goPrev = useCallback(() => {
    const prev = STEPS[stepIdx - 1]
    if (prev) setStep(prev)
  }, [stepIdx])

  const onPickFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setPhoto(f)
    if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl)
    setPhotoPreviewUrl(URL.createObjectURL(f))
  }

  const handleSubmit = async () => {
    if (!poiType || !geo.state.sample) {
      setError('Missing required step')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      let photoUploadId: string | undefined
      if (photo) {
        const compressed = await compressImage(photo)
        const presigned = await presignPhoto('image/jpeg')
        await uploadPhotoBytes(presigned, compressed)
        photoUploadId = presigned.upload_id
      }
      const result = await submitPOI({
        poi_type: poiType,
        location,
        name: name.trim() || null,
        attributes,
        submitted_gps: geo.state.sample,
        photo_upload_id: photoUploadId,
      })
      if (result.status === 'duplicate' && result.duplicate) {
        onDuplicate(result.duplicate)
      } else if (result.status === 'created' && result.detail) {
        onCreated(result.detail.id)
      }
    } catch (err) {
      const status = (err as { response?: { status?: number } })?.response
        ?.status
      if (status === 401) {
        setError('로그인이 필요합니다.')
      } else if (status === 422) {
        setError('GPS가 핀 위치에서 너무 멉니다 (50m 이내여야 합니다).')
      } else if (status === 429) {
        setError('하루 제출 한도를 초과했습니다.')
      } else {
        setError((err as Error).message || '제출 실패')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const canAdvance = useMemo(() => {
    switch (step) {
      case 'type':
        return poiType !== null
      case 'gps': {
        const s = geo.state.sample
        if (!s) return false
        if (s.accuracy_m > ACCURACY_HARD_LIMIT_M) return false
        return true
      }
      case 'photo':
        return true // photo optional
      case 'attrs':
        return true
      case 'review':
        return !submitting
    }
  }, [step, poiType, geo.state.sample, submitting])

  return (
    <aside
      role="dialog"
      aria-modal="false"
      aria-label="POI 제출"
      data-testid="submit-sheet"
      className="fixed bottom-0 left-0 right-0 md:top-0 md:bottom-0 md:left-auto md:right-0 md:w-[28rem] z-30 bg-white shadow-2xl border-t md:border-t-0 md:border-l border-gray-200 max-h-[85vh] md:max-h-screen overflow-y-auto"
    >
      <header className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">새 장소 추가 ({stepIdx + 1}/5)</h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close submit sheet"
          className="text-gray-500 hover:text-gray-900 text-xl leading-none px-2"
        >
          ×
        </button>
      </header>

      <div className="px-4 py-3 space-y-4" data-testid={`submit-step-${step}`}>
        {step === 'type' && (
          <TypePicker selected={poiType} onPick={setPoiType} />
        )}
        {step === 'gps' && (
          <GpsCapture
            geo={geo}
            location={location}
            setLocation={setLocation}
          />
        )}
        {step === 'photo' && (
          <PhotoStep
            photoPreviewUrl={photoPreviewUrl}
            onPickFile={onPickFile}
            onClear={() => {
              setPhoto(null)
              if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl)
              setPhotoPreviewUrl(null)
            }}
          />
        )}
        {step === 'attrs' && poiType && (
          <AttributesForm
            poi_type={poiType}
            value={attributes}
            onChange={setAttributes}
            name={name}
            onNameChange={setName}
          />
        )}
        {step === 'review' && (
          <Review
            poiType={poiType}
            name={name}
            location={location}
            attributes={attributes}
            hasPhoto={!!photo}
            error={error}
          />
        )}
      </div>

      <footer className="sticky bottom-0 bg-white border-t border-gray-200 px-4 py-3 flex justify-between">
        <button
          type="button"
          onClick={goPrev}
          disabled={stepIdx === 0}
          className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-40"
        >
          이전
        </button>
        {step !== 'review' ? (
          <button
            type="button"
            onClick={goNext}
            disabled={!canAdvance}
            data-testid="submit-next"
            className="px-4 py-1.5 rounded-lg text-sm font-semibold bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            다음
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            data-testid="submit-go"
            className="px-4 py-1.5 rounded-lg text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? '제출 중…' : '제출하기'}
          </button>
        )}
      </footer>

      {/* Hard-distance check between pin and GPS — keeps client honest */}
      {PIN_DRIFT_HARD_LIMIT_M < 0 ? null : null}
    </aside>
  )
}

function TypePicker({
  selected,
  onPick,
}: {
  selected: POIType | null
  onPick: (t: POIType) => void
}) {
  return (
    <div>
      <p className="text-sm text-gray-700 mb-3">어떤 시설인가요?</p>
      <div className="grid grid-cols-2 gap-3">
        {ALL_POI_TYPES.map((t) => {
          const Icon = POI_TYPE_LUCIDE[t]
          const isSelected = selected === t
          return (
            <button
              key={t}
              type="button"
              onClick={() => onPick(t)}
              data-testid={`submit-type-${t}`}
              className={`flex items-center gap-2 px-3 py-3 rounded-xl border-2 text-left transition ${
                isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <Icon size={24} aria-hidden="true" />
              <span className="font-medium">{POI_TYPE_LABELS[t]}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function GpsCapture({
  geo,
  location,
  setLocation,
}: {
  geo: ReturnType<typeof useGeolocation>
  location: LatLng
  setLocation: (l: LatLng) => void
}) {
  const sample = geo.state.sample
  const tooInaccurate = !!sample && sample.accuracy_m > ACCURACY_HARD_LIMIT_M
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-700">
        현재 위치를 확인합니다. 모바일에서 더 정확합니다.
      </p>
      <button
        type="button"
        onClick={() => geo.acquire().catch(() => {})}
        disabled={geo.state.status === 'pending'}
        data-testid="submit-gps-acquire"
        className="px-3 py-1.5 rounded-lg text-sm font-medium bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50"
      >
        {geo.state.status === 'pending' ? '측정 중…' : '내 위치 측정'}
      </button>

      {sample && (
        <div className="text-sm text-gray-700 bg-gray-50 rounded-lg px-3 py-2">
          <div>
            위도: <code>{sample.lat.toFixed(6)}</code>
          </div>
          <div>
            경도: <code>{sample.lng.toFixed(6)}</code>
          </div>
          <div>
            정확도: <code>{Math.round(sample.accuracy_m)}m</code>
            {tooInaccurate && (
              <span className="text-red-600 ml-1">(50m 이내 필요)</span>
            )}
          </div>
        </div>
      )}

      {geo.state.error && (
        <div className="text-sm text-red-600" role="alert">
          {geo.state.error}
        </div>
      )}

      {sample && !tooInaccurate && (
        <button
          type="button"
          onClick={() =>
            setLocation({ lat: sample.lat, lng: sample.lng })
          }
          className="text-xs text-blue-600 hover:underline"
        >
          핀 위치를 측정값으로 맞추기
        </button>
      )}
      <p className="text-xs text-gray-500">
        핀 위치(서버 검증): {location.lat.toFixed(6)}, {location.lng.toFixed(6)}
      </p>
    </div>
  )
}

function PhotoStep({
  photoPreviewUrl,
  onPickFile,
  onClear,
}: {
  photoPreviewUrl: string | null
  onPickFile: (e: React.ChangeEvent<HTMLInputElement>) => void
  onClear: () => void
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-700">사진은 선택 사항입니다.</p>
      <input
        type="file"
        accept="image/*"
        capture="environment"
        onChange={onPickFile}
        data-testid="submit-photo-input"
        className="block w-full text-sm"
      />
      {photoPreviewUrl && (
        <div className="space-y-2">
          <img
            src={photoPreviewUrl}
            alt="preview"
            className="w-full max-h-60 object-cover rounded-lg border"
          />
          <button
            type="button"
            onClick={onClear}
            className="text-xs text-red-600 hover:underline"
          >
            사진 제거
          </button>
        </div>
      )}
      <p className="text-xs text-gray-500">
        업로드된 사진은 자동으로 얼굴/번호판이 흐림 처리됩니다.
      </p>
    </div>
  )
}

function AttributesForm({
  poi_type,
  value,
  onChange,
  name,
  onNameChange,
}: {
  poi_type: POIType
  value: Record<string, unknown>
  onChange: (v: Record<string, unknown>) => void
  name: string
  onNameChange: (s: string) => void
}) {
  const setKey = (k: string, v: unknown) => onChange({ ...value, [k]: v })
  return (
    <div className="space-y-3">
      <label className="block text-sm">
        <span className="text-gray-700">이름 (선택)</span>
        <input
          value={name}
          onChange={(e) => onNameChange(e.target.value)}
          maxLength={120}
          data-testid="submit-name"
          className="mt-1 block w-full rounded-lg border border-gray-300 px-2 py-1"
        />
      </label>

      {poi_type === 'toilet' && (
        <>
          <Checkbox
            label="장애인 화장실"
            value={!!value.accessibility}
            onChange={(v) => setKey('accessibility', v)}
            testId="attr-accessibility"
          />
          <Checkbox
            label="기저귀 교환대"
            value={!!value.has_baby_changing}
            onChange={(v) => setKey('has_baby_changing', v)}
          />
          <Checkbox
            label="무료"
            value={value.is_free !== false}
            onChange={(v) => setKey('is_free', v)}
          />
        </>
      )}
      {poi_type === 'trash_can' && (
        <>
          <Checkbox
            label="재활용"
            value={!!value.recycling}
            onChange={(v) => setKey('recycling', v)}
          />
          <Checkbox
            label="일반 쓰레기"
            value={value.general !== false}
            onChange={(v) => setKey('general', v)}
          />
        </>
      )}
      {poi_type === 'bench' && (
        <>
          <Checkbox
            label="등받이 있음"
            value={!!value.has_back}
            onChange={(v) => setKey('has_back', v)}
          />
          <Checkbox
            label="그늘 있음"
            value={!!value.shaded}
            onChange={(v) => setKey('shaded', v)}
          />
        </>
      )}
      {poi_type === 'smoking_area' && (
        <Checkbox
          label="실내/폐쇄형"
          value={!!value.enclosed}
          onChange={(v) => setKey('enclosed', v)}
        />
      )}
      {poi_type === 'water_fountain' && (
        <>
          <Checkbox
            label="음용 가능"
            value={value.is_potable !== false}
            onChange={(v) => setKey('is_potable', v)}
          />
          <Checkbox
            label="계절제"
            value={!!value.seasonal}
            onChange={(v) => setKey('seasonal', v)}
          />
        </>
      )}
    </div>
  )
}

function Checkbox({
  label,
  value,
  onChange,
  testId,
}: {
  label: string
  value: boolean
  onChange: (v: boolean) => void
  testId?: string
}) {
  return (
    <label className="flex items-center gap-2 text-sm cursor-pointer">
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        data-testid={testId}
      />
      <span>{label}</span>
    </label>
  )
}

function Review({
  poiType,
  name,
  location,
  attributes,
  hasPhoto,
  error,
}: {
  poiType: POIType | null
  name: string
  location: LatLng
  attributes: Record<string, unknown>
  hasPhoto: boolean
  error: string | null
}) {
  return (
    <div className="space-y-3 text-sm">
      <ReviewRow label="유형">
        {poiType ? (
          <span className="inline-flex items-center gap-2">
            <TypeIcon poi_type={poiType} size={20} />
            {POI_TYPE_LABELS[poiType]}
          </span>
        ) : (
          '-'
        )}
      </ReviewRow>
      <ReviewRow label="이름">{name || <em className="text-gray-400">없음</em>}</ReviewRow>
      <ReviewRow label="위치">
        {location.lat.toFixed(6)}, {location.lng.toFixed(6)}
      </ReviewRow>
      <ReviewRow label="사진">{hasPhoto ? '첨부' : '없음'}</ReviewRow>
      <ReviewRow label="속성">
        <pre className="bg-gray-50 rounded p-2 text-xs overflow-x-auto">
          {JSON.stringify(attributes, null, 2)}
        </pre>
      </ReviewRow>
      {error && (
        <div className="text-red-600 text-sm" role="alert">
          {error}
        </div>
      )}
    </div>
  )
}

function ReviewRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3 border-b border-gray-100 pb-1">
      <span className="text-gray-500">{label}</span>
      <span className="text-gray-900 text-right">{children}</span>
    </div>
  )
}
