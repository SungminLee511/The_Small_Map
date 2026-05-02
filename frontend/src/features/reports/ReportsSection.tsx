import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { confirmReport, fetchReportsForPOI } from '@/api/reports'
import { useMe } from '@/features/auth/useMe'
import { REPORT_TYPE_ICONS, REPORT_TYPE_LABELS } from '@/types/report'
import type { Report } from '@/types/report'
import type { POIDetail } from '@/types/poi'
import { ReportSubmitModal } from './ReportSubmitModal'

interface ReportsSectionProps {
  poi: POIDetail
}

/**
 * Active-reports section in the POI detail panel.
 *
 * Uses ``poi.active_reports`` (Phase 3.3.3 — server pre-loads up to 5),
 * but also re-queries via ``fetchReportsForPOI`` when the user opens
 * the panel so freshly-resolved or freshly-submitted reports surface
 * within the staleTime window. The "신고하기" button opens the
 * submission modal (Phase 3.4.1).
 */
export function ReportsSection({ poi }: ReportsSectionProps) {
  const { data: me } = useMe()
  const [submitOpen, setSubmitOpen] = useState(false)

  const initial: Report[] = (poi.active_reports as Report[] | undefined) ?? []

  const reportsQ = useQuery({
    queryKey: ['poi-reports', poi.id],
    queryFn: () => fetchReportsForPOI(poi.id),
    enabled: !!poi.id,
    staleTime: 30_000,
    initialData: initial,
  })

  const reports = reportsQ.data ?? []

  return (
    <section
      className="pt-3 border-t border-gray-100"
      data-testid="reports-section"
    >
      <header className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">
          활성 신고 {reports.length > 0 && (
            <span className="ml-1 text-red-600">{reports.length}</span>
          )}
        </h3>
        {me && (
          <button
            type="button"
            onClick={() => setSubmitOpen(true)}
            data-testid="open-report-modal-button"
            className="text-xs font-medium text-red-600 hover:text-red-700 hover:underline"
          >
            + 신고하기
          </button>
        )}
      </header>

      {reports.length === 0 ? (
        <p className="text-xs text-gray-500" data-testid="reports-empty">
          신고 내역 없음
        </p>
      ) : (
        <ul className="space-y-2">
          {reports.map((r) => (
            <ReportRow key={r.id} report={r} poiId={poi.id} />
          ))}
        </ul>
      )}

      {submitOpen && (
        <ReportSubmitModal
          poiId={poi.id}
          onClose={() => setSubmitOpen(false)}
        />
      )}
    </section>
  )
}

function ReportRow({ report, poiId }: { report: Report; poiId: string }) {
  const { data: me } = useMe()
  const qc = useQueryClient()
  const confirmMut = useMutation({
    mutationFn: () => confirmReport(report.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['poi', poiId] })
      qc.invalidateQueries({ queryKey: ['poi-reports', poiId] })
    },
  })

  const isMine = me?.id === report.reporter_id
  const errStatus = (
    confirmMut.error as { response?: { status?: number } } | null
  )?.response?.status
  const confirmDisabled = !me || isMine || confirmMut.isPending || confirmMut.isSuccess
  const confirmLabel =
    confirmMut.isSuccess
      ? '확인됨'
      : errStatus === 409
        ? '이미 확인'
        : isMine
          ? '내 신고'
          : '저도 봤어요'

  return (
    <li
      className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm"
      data-testid="report-row"
      data-report-id={report.id}
    >
      <div className="flex items-center gap-2">
        <span className="text-lg" aria-hidden="true">
          {REPORT_TYPE_ICONS[report.report_type]}
        </span>
        <div className="flex-1 min-w-0">
          <div className="font-medium">
            {REPORT_TYPE_LABELS[report.report_type]}
          </div>
          {report.description && (
            <div className="text-xs text-gray-600 truncate">
              {report.description}
            </div>
          )}
          <div className="text-[10px] text-gray-500 mt-0.5">
            {timeAgo(report.created_at)} · 확인 {report.confirmation_count}
          </div>
        </div>
        <button
          type="button"
          onClick={() => confirmMut.mutate()}
          disabled={confirmDisabled}
          data-testid="confirm-report-button"
          className="text-xs font-semibold px-2 py-1 rounded-md bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {confirmLabel}
        </button>
      </div>
    </li>
  )
}

function timeAgo(iso: string): string {
  const ts = new Date(iso).getTime()
  if (Number.isNaN(ts)) return iso
  const elapsed = (Date.now() - ts) / 1000
  if (elapsed < 60) return '방금'
  if (elapsed < 3600) return `${Math.floor(elapsed / 60)}분 전`
  if (elapsed < 86400) return `${Math.floor(elapsed / 3600)}시간 전`
  return `${Math.floor(elapsed / 86400)}일 전`
}
