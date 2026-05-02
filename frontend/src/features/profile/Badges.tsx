import type { POIDetail } from '@/types/poi'
import type { UserMe } from '@/types/user'

interface BadgesProps {
  me: UserMe
  submissions: POIDetail[]
  confirmations: POIDetail[]
}

interface Badge {
  id: string
  emoji: string
  label: string
  description: string
  earned: boolean
}

const TRUSTED_THRESHOLD = 50

/**
 * Phase 4.3.2 — small badges grid on the profile page. v1 has three:
 *   - Trusted (rep >= 50)
 *   - First Submission (any verified POI under user:<self>)
 *   - Confirmer (>= 10 confirmations of others' POIs)
 * Plan mentions "First 100 Mappers" as a curated honour — needs server
 * coordination so it's omitted for v1.
 */
export function Badges({ me, submissions, confirmations }: BadgesProps) {
  const verifiedSubs = submissions.filter(
    (s) => s.verification_status === 'verified',
  )
  const badges: Badge[] = [
    {
      id: 'trusted',
      emoji: '⭐',
      label: 'Trusted',
      description: `평판 ${TRUSTED_THRESHOLD} 이상`,
      earned: me.reputation >= TRUSTED_THRESHOLD,
    },
    {
      id: 'first-submission',
      emoji: '📍',
      label: 'First Submission',
      description: '첫 POI 등록',
      earned: verifiedSubs.length >= 1 || submissions.length >= 1,
    },
    {
      id: 'confirmer',
      emoji: '🤝',
      label: 'Confirmer',
      description: '10개 이상 확인',
      earned: confirmations.length >= 10,
    },
  ]

  return (
    <ul
      className="grid grid-cols-3 gap-2"
      data-testid="badges-list"
      aria-label="배지"
    >
      {badges.map((b) => (
        <li
          key={b.id}
          data-testid={`badge-${b.id}`}
          data-earned={b.earned ? 'true' : 'false'}
          className={`rounded-lg border px-2 py-3 text-center ${
            b.earned
              ? 'border-amber-300 bg-amber-50 text-amber-900'
              : 'border-gray-200 bg-gray-50 text-gray-400 opacity-60'
          }`}
          title={b.description}
        >
          <div className="text-2xl" aria-hidden="true">
            {b.emoji}
          </div>
          <div className="text-xs font-semibold">{b.label}</div>
          <div className="text-[10px] mt-0.5">{b.description}</div>
        </li>
      ))}
    </ul>
  )
}
