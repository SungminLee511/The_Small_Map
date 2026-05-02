import { useMutation, useQueryClient } from '@tanstack/react-query'
import { confirmPOI, proposeRemoval } from '@/api/pois'
import { useMe } from '@/features/auth/useMe'
import type { POIDetail } from '@/types/poi'

interface StalePromptProps {
  poi: POIDetail
}

/**
 * Stale-POI re-verification prompt (Phase 4.3.1).
 *
 * Server marks ``is_stale`` when last_verified_at > 180d ago AND no
 * active reports. We show a yellow banner with two actions:
 *   - "여기 있어요"     → confirmPOI (refreshes last_verified_at)
 *   - "더 이상 없어요"  → proposeRemoval (3 of these auto-soft-delete)
 * Hidden when the user is logged out, when it's their own submission,
 * or when the POI isn't stale.
 */
export function StalePrompt({ poi }: StalePromptProps) {
  const { data: me } = useMe()
  const qc = useQueryClient()
  const confirmMut = useMutation({
    mutationFn: () => confirmPOI(poi.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['poi', poi.id] })
      qc.invalidateQueries({ queryKey: ['pois'] })
    },
  })
  const removeMut = useMutation({
    mutationFn: () => proposeRemoval(poi.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['poi', poi.id] })
      qc.invalidateQueries({ queryKey: ['pois'] })
    },
  })

  if (!poi.is_stale) return null
  if (!me) return null
  if (poi.source === `user:${me.id}`) return null

  const lastVerified = poi.last_verified_at
    ? formatRelative(poi.last_verified_at)
    : '알 수 없음'

  const removeStatus = (
    removeMut.error as { response?: { status?: number } } | null
  )?.response?.status

  return (
    <div
      className="rounded-lg border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm"
      data-testid="stale-prompt"
    >
      <p className="font-medium text-yellow-900">
        🕐 {lastVerified} 마지막 확인됐어요. 아직 여기 있나요?
      </p>
      <div className="mt-2 flex gap-2">
        <button
          type="button"
          onClick={() => confirmMut.mutate()}
          disabled={confirmMut.isPending || confirmMut.isSuccess}
          data-testid="stale-confirm-button"
          className="flex-1 px-2 py-1.5 rounded-md text-xs font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
        >
          {confirmMut.isSuccess ? '확인됨' : '여기 있어요'}
        </button>
        <button
          type="button"
          onClick={() => removeMut.mutate()}
          disabled={
            removeMut.isPending ||
            removeMut.isSuccess ||
            (removeMut.data?.soft_deleted ?? false)
          }
          data-testid="stale-remove-button"
          className="flex-1 px-2 py-1.5 rounded-md text-xs font-semibold bg-gray-700 text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {removeMut.data?.soft_deleted
            ? '삭제됨'
            : removeMut.isSuccess
              ? '제안됨'
              : '더 이상 없어요'}
        </button>
      </div>
      {removeMut.data && !removeMut.data.soft_deleted && (
        <p className="mt-1 text-xs text-gray-600">
          제안 {removeMut.data.proposal_count}/{removeMut.data.threshold}
        </p>
      )}
      {removeStatus === 409 && (
        <p className="mt-1 text-xs text-red-600">이미 제안하셨습니다.</p>
      )}
      {removeStatus === 403 && (
        <p className="mt-1 text-xs text-red-600">평판이 부족합니다.</p>
      )}
    </div>
  )
}

function formatRelative(iso: string): string {
  const ts = new Date(iso).getTime()
  if (Number.isNaN(ts)) return iso
  const days = Math.floor((Date.now() - ts) / 86400000)
  if (days < 30) return `${days}일 전`
  if (days < 365) return `${Math.floor(days / 30)}개월 전`
  return `${Math.floor(days / 365)}년 전`
}
