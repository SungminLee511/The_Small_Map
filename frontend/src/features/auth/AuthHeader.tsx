import { kakaoAuthorizeUrl } from '@/api/auth'
import { useLogout, useMe } from './useMe'

/**
 * Top-right header showing login state. Pinned overlay so it works on top
 * of the map without disturbing layout. Login button kicks off the Kakao
 * OAuth redirect (server-side ``/auth/kakao/authorize``).
 */
export function AuthHeader() {
  const { data: me, isLoading } = useMe()
  const logoutMut = useLogout()

  if (isLoading) {
    return (
      <div
        className="absolute top-4 right-4 z-20 bg-white/90 backdrop-blur rounded-lg px-3 py-1 shadow-md text-sm text-gray-500"
        data-testid="auth-header"
      >
        …
      </div>
    )
  }

  if (!me) {
    return (
      <div
        className="absolute top-4 right-4 z-20"
        data-testid="auth-header"
      >
        <a
          href={kakaoAuthorizeUrl()}
          className="inline-flex items-center gap-2 bg-yellow-300 hover:bg-yellow-400 text-gray-900 px-3 py-1.5 rounded-lg shadow-md text-sm font-semibold"
          data-testid="auth-login-button"
        >
          카카오로 로그인
        </a>
      </div>
    )
  }

  return (
    <div
      className="absolute top-4 right-4 z-20 bg-white/90 backdrop-blur rounded-lg px-3 py-1.5 shadow-md flex items-center gap-2 text-sm"
      data-testid="auth-header"
    >
      {me.avatar_url ? (
        <img
          src={me.avatar_url}
          alt=""
          className="w-7 h-7 rounded-full object-cover"
          aria-hidden="true"
        />
      ) : (
        <span
          className="w-7 h-7 rounded-full bg-gray-200 inline-flex items-center justify-center text-xs font-bold"
          aria-hidden="true"
        >
          {me.display_name.slice(0, 1)}
        </span>
      )}
      <a
        href="/me"
        className="font-medium text-gray-900 hover:underline"
        data-testid="auth-user-name"
      >
        {me.display_name}
      </a>
      <span className="text-xs text-gray-500" title="평판">
        ⭐ {me.reputation}
      </span>
      <button
        type="button"
        onClick={() => logoutMut.mutate()}
        disabled={logoutMut.isPending}
        className="text-xs text-gray-500 hover:text-red-600 hover:underline ml-1 disabled:opacity-50"
        data-testid="auth-logout-button"
      >
        로그아웃
      </button>
    </div>
  )
}
