import { useT } from '@/i18n/I18nProvider'
import { LanguageToggle } from '@/i18n/LanguageToggle'

interface StaticLayoutProps {
  title: string
  children: React.ReactNode
}

/** Simple framed layout shared by /about /privacy /terms. */
export function StaticLayout({ title, children }: StaticLayoutProps) {
  const t = useT()
  return (
    <main
      className="max-w-3xl mx-auto px-4 py-8 text-gray-900"
      data-testid="static-layout"
    >
      <header className="flex items-center justify-between border-b border-gray-200 pb-3 mb-4">
        <a
          href="/"
          className="text-lg font-bold hover:underline"
        >
          {t('app.title')}
        </a>
        <LanguageToggle />
      </header>
      <h1 className="text-2xl font-bold mb-4">{title}</h1>
      <div className="prose prose-sm max-w-none space-y-3 leading-relaxed">
        {children}
      </div>
      <footer className="mt-8 pt-3 border-t border-gray-200 text-xs text-gray-500 flex gap-3">
        <a href="/" className="hover:underline">
          {t('nav.map')}
        </a>
        <a href="/about" className="hover:underline">
          {t('nav.about')}
        </a>
        <a href="/privacy" className="hover:underline">
          {t('nav.privacy')}
        </a>
        <a href="/terms" className="hover:underline">
          {t('nav.terms')}
        </a>
      </footer>
    </main>
  )
}
