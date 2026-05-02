import { useI18n } from './I18nProvider'

/**
 * Tiny KO/EN segmented toggle, designed to sit next to the auth header.
 */
export function LanguageToggle() {
  const { locale, setLocale } = useI18n()
  return (
    <div
      role="radiogroup"
      aria-label="Language"
      data-testid="language-toggle"
      className="inline-flex items-center bg-white/90 backdrop-blur rounded-full shadow-sm overflow-hidden text-xs font-semibold"
    >
      <button
        type="button"
        role="radio"
        aria-checked={locale === 'ko'}
        onClick={() => setLocale('ko')}
        data-testid="language-ko"
        className={`px-2 py-1 ${
          locale === 'ko'
            ? 'bg-blue-500 text-white'
            : 'text-gray-700 hover:bg-gray-100'
        }`}
      >
        KO
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={locale === 'en'}
        onClick={() => setLocale('en')}
        data-testid="language-en"
        className={`px-2 py-1 ${
          locale === 'en'
            ? 'bg-blue-500 text-white'
            : 'text-gray-700 hover:bg-gray-100'
        }`}
      >
        EN
      </button>
    </div>
  )
}
