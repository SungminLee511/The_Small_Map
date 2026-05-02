import { useT } from '@/i18n/I18nProvider'

/**
 * Tiny footer rendered in a corner of the map screen so the legally-
 * required static pages are always reachable. Uses small text to stay
 * out of the way on mobile.
 */
export function Footer() {
  const t = useT()
  return (
    <footer
      className="absolute bottom-2 left-2 z-10 flex gap-2 text-[10px] text-gray-500 bg-white/70 backdrop-blur rounded px-2 py-1 pointer-events-auto"
      data-testid="map-footer"
    >
      <a href="/about" className="hover:underline">
        {t('nav.about')}
      </a>
      <span aria-hidden="true">·</span>
      <a href="/privacy" className="hover:underline">
        {t('nav.privacy')}
      </a>
      <span aria-hidden="true">·</span>
      <a href="/terms" className="hover:underline">
        {t('nav.terms')}
      </a>
    </footer>
  )
}
