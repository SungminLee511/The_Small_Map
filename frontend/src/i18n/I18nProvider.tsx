import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { LOCALES, messages } from './messages'
import type { Locale, MessageKey } from './messages'

const STORAGE_KEY = 'smallmap.locale'

interface I18nContextShape {
  locale: Locale
  setLocale: (loc: Locale) => void
  t: (key: MessageKey) => string
}

const I18nContext = createContext<I18nContextShape | null>(null)

function detectLocale(): Locale {
  if (typeof window === 'undefined') return 'ko'
  const stored = window.localStorage.getItem(STORAGE_KEY) as Locale | null
  if (stored && LOCALES.includes(stored)) return stored
  const nav = (navigator?.language ?? 'ko').toLowerCase()
  return nav.startsWith('ko') ? 'ko' : 'en'
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => detectLocale())

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale
    }
  }, [locale])

  const setLocale = useCallback((loc: Locale) => {
    setLocaleState(loc)
    try {
      window.localStorage.setItem(STORAGE_KEY, loc)
    } catch {
      /* storage may be disabled in some browsers — non-fatal */
    }
  }, [])

  const t = useCallback(
    (key: MessageKey): string => {
      // Korean first, English fallback.
      return (
        (messages[locale] as Record<string, string>)[key] ??
        (messages.ko as Record<string, string>)[key] ??
        key
      )
    },
    [locale],
  )

  const value = useMemo(
    () => ({ locale, setLocale, t }),
    [locale, setLocale, t],
  )
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n(): I18nContextShape {
  const ctx = useContext(I18nContext)
  if (ctx === null) {
    throw new Error('useI18n must be used inside <I18nProvider>')
  }
  return ctx
}

export function useT(): (key: MessageKey) => string {
  return useI18n().t
}
