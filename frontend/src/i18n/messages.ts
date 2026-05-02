/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Centralised translation dictionaries (Phase 4.3.3).
 *
 * Korean is primary (the v1 audience). English is a fallback for the
 * About/Privacy/Terms pages and core nav. We keep this lib-free —
 * react-i18next would add ~30kB for a single dropdown.
 */

export type Locale = 'ko' | 'en'

export const LOCALES: Locale[] = ['ko', 'en']

export const messages = {
  ko: {
    'app.title': '소소한 지도',
    'app.tagline': '동네의 작은 시설을 한 눈에',

    'nav.about': '소개',
    'nav.privacy': '개인정보',
    'nav.terms': '이용약관',
    'nav.profile': '내 프로필',
    'nav.map': '지도로',

    'auth.loginKakao': '카카오로 로그인',
    'auth.logout': '로그아웃',
    'auth.reputation': '평판',

    'filter.all': '전체',
    'filter.none': '없음',

    'common.loading': '로딩 중…',
    'common.error': '오류가 발생했습니다',
    'common.empty': '내용이 없습니다',
    'common.cancel': '취소',
    'common.close': '닫기',
    'common.back': '뒤로',
  },
  en: {
    'app.title': 'The Small Map',
    'app.tagline': 'Tiny city amenities at a glance',

    'nav.about': 'About',
    'nav.privacy': 'Privacy',
    'nav.terms': 'Terms',
    'nav.profile': 'Profile',
    'nav.map': 'Map',

    'auth.loginKakao': 'Sign in with Kakao',
    'auth.logout': 'Sign out',
    'auth.reputation': 'Rep',

    'filter.all': 'All',
    'filter.none': 'None',

    'common.loading': 'Loading…',
    'common.error': 'Something went wrong',
    'common.empty': 'Nothing to show',
    'common.cancel': 'Cancel',
    'common.close': 'Close',
    'common.back': 'Back',
  },
} as const satisfies Record<Locale, Record<string, string>>

export type MessageKey = keyof (typeof messages)['ko']
