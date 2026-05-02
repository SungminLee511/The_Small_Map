import { useQuery } from '@tanstack/react-query'
import { kakaoAuthorizeUrl } from '@/api/auth'
import {
  fetchMyConfirmations,
  fetchMyReputationEvents,
  fetchMySubmissions,
} from '@/api/me'
import { useMe } from '@/features/auth/useMe'
import { POI_TYPE_LABELS } from '@/types/poi'
import { TypeIcon } from '@/features/map/TypeIcon'
import { Skeleton } from '@/components/Skeleton'
import type { POIDetail } from '@/types/poi'
import { Badges } from './Badges'
import { ReputationGraph } from './ReputationGraph'

/** Server-rendered-via-CSR /me page: submissions, confirmations, reputation. */
export function ProfilePage() {
  const meQ = useMe()
  const me = meQ.data

  const submissionsQ = useQuery({
    queryKey: ['me', 'submissions'],
    queryFn: fetchMySubmissions,
    enabled: !!me,
    staleTime: 30_000,
  })
  const confirmationsQ = useQuery({
    queryKey: ['me', 'confirmations'],
    queryFn: fetchMyConfirmations,
    enabled: !!me,
    staleTime: 30_000,
  })
  const repEventsQ = useQuery({
    queryKey: ['me', 'reputation'],
    queryFn: fetchMyReputationEvents,
    enabled: !!me,
    staleTime: 30_000,
  })

  if (meQ.isLoading) {
    return (
      <main className="max-w-3xl mx-auto px-4 py-10 text-gray-500">
        로딩 중…
      </main>
    )
  }
  if (!me) {
    return (
      <main className="max-w-3xl mx-auto px-4 py-10">
        <h1 className="text-2xl font-bold mb-4">내 프로필</h1>
        <p className="text-gray-700 mb-4">
          로그인 후 이용할 수 있습니다.
        </p>
        <a
          href={kakaoAuthorizeUrl()}
          data-testid="profile-login-link"
          className="inline-flex items-center bg-yellow-300 hover:bg-yellow-400 text-gray-900 px-4 py-2 rounded-lg font-semibold"
        >
          카카오로 로그인
        </a>
      </main>
    )
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-8" data-testid="profile-page">
      <header className="flex items-center gap-4 pb-4 border-b border-gray-200">
        {me.avatar_url ? (
          <img
            src={me.avatar_url}
            alt=""
            className="w-14 h-14 rounded-full object-cover"
          />
        ) : (
          <span className="w-14 h-14 rounded-full bg-gray-200 inline-flex items-center justify-center text-xl font-bold">
            {me.display_name.slice(0, 1)}
          </span>
        )}
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{me.display_name}</h1>
          {me.email && <p className="text-sm text-gray-500">{me.email}</p>}
        </div>
        <div
          className="text-right"
          data-testid="profile-reputation"
          aria-label="평판"
        >
          <div className="text-2xl font-bold">⭐ {me.reputation}</div>
          <div className="text-xs text-gray-500">평판</div>
        </div>
      </header>

      <section className="mt-6" data-testid="profile-rep-history">
        <h2 className="text-lg font-semibold mb-2">평판 추이</h2>
        <div className="bg-white border border-gray-200 rounded-lg px-3 py-3">
          <ReputationGraph events={repEventsQ.data ?? []} />
        </div>
      </section>

      <section className="mt-6" data-testid="profile-badges">
        <h2 className="text-lg font-semibold mb-2">배지</h2>
        <Badges
          me={me}
          submissions={submissionsQ.data ?? []}
          confirmations={confirmationsQ.data ?? []}
        />
      </section>

      <Section
        title="내가 등록한 장소"
        emptyText="아직 등록한 장소가 없습니다."
        items={submissionsQ.data ?? null}
        loading={submissionsQ.isLoading}
        testId="profile-submissions"
      />

      <Section
        title="내가 확인한 장소"
        emptyText="아직 확인한 장소가 없습니다."
        items={confirmationsQ.data ?? null}
        loading={confirmationsQ.isLoading}
        testId="profile-confirmations"
      />

      <p className="mt-6 text-sm">
        <a href="/" className="text-blue-600 hover:underline">
          ← 지도로 돌아가기
        </a>
      </p>
    </main>
  )
}

function Section({
  title,
  emptyText,
  items,
  loading,
  testId,
}: {
  title: string
  emptyText: string
  items: POIDetail[] | null
  loading: boolean
  testId: string
}) {
  return (
    <section className="mt-8" data-testid={testId}>
      <h2 className="text-lg font-semibold mb-3">{title}</h2>
      {loading && (
        <Skeleton
          height={56}
          rows={3}
          className="w-full"
          testId={`${testId}-skeleton`}
        />
      )}
      {!loading && (!items || items.length === 0) && (
        <p className="text-gray-500 text-sm">{emptyText}</p>
      )}
      {!loading && items && items.length > 0 && (
        <ul className="space-y-2">
          {items.map((p) => (
            <li
              key={p.id}
              className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg px-3 py-2"
            >
              <TypeIcon poi_type={p.poi_type} size={28} />
              <div className="flex-1 min-w-0">
                <a
                  href={`/?poi=${p.id}`}
                  className="font-medium text-gray-900 hover:underline truncate block"
                >
                  {p.name ?? POI_TYPE_LABELS[p.poi_type]}
                </a>
                <div className="text-xs text-gray-500">
                  {POI_TYPE_LABELS[p.poi_type]} · {p.verification_count} 확인
                </div>
              </div>
              {p.verification_status === 'unverified' ? (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-800">
                  미확인
                </span>
              ) : (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-green-100 text-green-800">
                  확인됨
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
