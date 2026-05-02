import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { resolveReport } from '@/api/reports'
import type { Report } from '@/types/report'

interface ReportResolveModalProps {
  report: Report
  poiId: string
  onClose: () => void
}

const HOUR_MS = 3_600_000

/**
 * Resolve modal — required note + optional photo URL. Server enforces
 * the "non-reporter must wait 24h" rule (returns 403 + Retry-After);
 * we surface that here as a friendly message.
 */
export function ReportResolveModal({
  report,
  poiId,
  onClose,
}: ReportResolveModalProps) {
  const [note, setNote] = useState('')
  const [photoUrl, setPhotoUrl] = useState('')
  const qc = useQueryClient()

  const mut = useMutation({
    mutationFn: () =>
      resolveReport(report.id, {
        resolution_note: note.trim(),
        photo_url: photoUrl.trim() || null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['poi', poiId] })
      qc.invalidateQueries({ queryKey: ['poi-reports', poiId] })
      qc.invalidateQueries({ queryKey: ['pois'] })
      onClose()
    },
  })

  const errStatus = (
    mut.error as { response?: { status?: number; headers?: Record<string, string> } } | null
  )?.response?.status
  const retryAfter =
    (
      mut.error as {
        response?: { headers?: Record<string, string> }
      } | null
    )?.response?.headers?.['retry-after'] ?? null
  const errMsg =
    errStatus === 403
      ? `다른 사용자의 신고는 24시간 후에 해결 가능합니다. (남은 시간: ${formatRetry(retryAfter)})`
      : errStatus === 404
        ? '신고를 찾을 수 없습니다.'
        : mut.error
          ? '해결 실패'
          : null

  const canSubmit = note.trim().length > 0 && !mut.isPending

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center px-4"
      role="dialog"
      aria-modal="true"
      aria-label="신고 해결"
      data-testid="report-resolve-modal"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[85vh] overflow-y-auto">
        <header className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">신고 해결</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close resolve modal"
            className="text-gray-500 hover:text-gray-900 text-xl leading-none px-2"
          >
            ×
          </button>
        </header>

        <div className="px-4 py-3 space-y-3">
          <label className="block text-sm">
            <span className="text-gray-700">해결 메모 (필수)</span>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              maxLength={500}
              rows={3}
              required
              data-testid="resolve-note"
              placeholder="어떻게 해결됐나요?"
              className="mt-1 block w-full rounded-lg border border-gray-300 px-2 py-1 text-sm"
            />
            <span className="text-xs text-gray-400">{note.length}/500</span>
          </label>

          <label className="block text-sm">
            <span className="text-gray-700">사진 URL (선택)</span>
            <input
              type="url"
              value={photoUrl}
              onChange={(e) => setPhotoUrl(e.target.value)}
              maxLength={1024}
              data-testid="resolve-photo-url"
              placeholder="https://…"
              className="mt-1 block w-full rounded-lg border border-gray-300 px-2 py-1 text-sm"
            />
          </label>

          {errMsg && (
            <p className="text-sm text-red-600" role="alert">
              {errMsg}
            </p>
          )}
        </div>

        <footer className="sticky bottom-0 bg-white border-t border-gray-200 px-4 py-3 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200"
          >
            취소
          </button>
          <button
            type="button"
            onClick={() => mut.mutate()}
            disabled={!canSubmit}
            data-testid="resolve-submit-button"
            className="px-4 py-1.5 rounded-lg text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mut.isPending ? '저장 중…' : '해결됨으로 표시'}
          </button>
        </footer>
      </div>
    </div>
  )
}

function formatRetry(retryAfterSeconds: string | null): string {
  if (!retryAfterSeconds) return '잠시 후'
  const sec = Number(retryAfterSeconds)
  if (!Number.isFinite(sec)) return '잠시 후'
  const ms = sec * 1000
  if (ms < HOUR_MS) return `${Math.ceil(sec / 60)}분`
  return `${Math.ceil(sec / 3600)}시간`
}
