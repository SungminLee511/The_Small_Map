import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { submitReport } from '@/api/reports'
import { ALL_REPORT_TYPES, REPORT_TYPE_ICONS, REPORT_TYPE_LABELS } from '@/types/report'
import type { ReportType } from '@/types/report'

interface ReportSubmitModalProps {
  poiId: string
  onClose: () => void
  onSubmitted?: (reportId: string) => void
}

/**
 * "Report an issue" modal. Pick a type from the icon grid, optional
 * description, optional photo URL (the upload-to-R2 dance is reused
 * from Phase 2.3.2 — for now we accept a URL directly to keep this
 * commit focused).
 */
export function ReportSubmitModal({
  poiId,
  onClose,
  onSubmitted,
}: ReportSubmitModalProps) {
  const [type, setType] = useState<ReportType | null>(null)
  const [description, setDescription] = useState('')
  const qc = useQueryClient()

  const mut = useMutation({
    mutationFn: () =>
      submitReport(poiId, {
        report_type: type as ReportType,
        description: description.trim() || null,
      }),
    onSuccess: (report) => {
      qc.invalidateQueries({ queryKey: ['poi', poiId] })
      qc.invalidateQueries({ queryKey: ['poi-reports', poiId] })
      qc.invalidateQueries({ queryKey: ['pois'] })
      onSubmitted?.(report.id)
      onClose()
    },
  })

  const errStatus = (
    mut.error as { response?: { status?: number } } | null
  )?.response?.status
  const errMsg =
    errStatus === 401
      ? '로그인이 필요합니다.'
      : errStatus === 429
        ? '하루 신고 한도를 초과했습니다.'
        : errStatus === 404
          ? 'POI를 찾을 수 없습니다.'
          : mut.error
            ? '신고 실패'
            : null

  return (
    <div
      className="fixed inset-0 z-40 bg-black/40 flex items-center justify-center px-4"
      role="dialog"
      aria-modal="true"
      aria-label="문제 신고"
      data-testid="report-submit-modal"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[85vh] overflow-y-auto">
        <header className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">문제 신고</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close report modal"
            className="text-gray-500 hover:text-gray-900 text-xl leading-none px-2"
          >
            ×
          </button>
        </header>

        <div className="px-4 py-3 space-y-3">
          <p className="text-sm text-gray-700">어떤 문제인가요?</p>
          <div className="grid grid-cols-3 gap-2">
            {ALL_REPORT_TYPES.map((t) => {
              const isSelected = type === t
              return (
                <button
                  key={t}
                  type="button"
                  onClick={() => setType(t)}
                  data-testid={`report-type-${t}`}
                  className={`flex flex-col items-center gap-1 px-2 py-3 rounded-xl border-2 transition ${
                    isSelected
                      ? 'border-red-500 bg-red-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-2xl" aria-hidden="true">
                    {REPORT_TYPE_ICONS[t]}
                  </span>
                  <span className="text-xs font-medium">
                    {REPORT_TYPE_LABELS[t]}
                  </span>
                </button>
              )
            })}
          </div>

          <label className="block text-sm">
            <span className="text-gray-700">설명 (선택)</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              rows={3}
              data-testid="report-description"
              className="mt-1 block w-full rounded-lg border border-gray-300 px-2 py-1 text-sm"
              placeholder="추가 정보가 있다면 적어주세요"
            />
            <span className="text-xs text-gray-400">
              {description.length}/500
            </span>
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
            disabled={!type || mut.isPending}
            data-testid="report-submit-button"
            className="px-4 py-1.5 rounded-lg text-sm font-semibold bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mut.isPending ? '신고 중…' : '신고'}
          </button>
        </footer>
      </div>
    </div>
  )
}
