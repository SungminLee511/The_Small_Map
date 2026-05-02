import { useI18n } from '@/i18n/I18nProvider'
import { StaticLayout } from './StaticLayout'

export function AboutPage() {
  const { locale } = useI18n()
  return (
    <StaticLayout title={locale === 'ko' ? '소개' : 'About'}>
      <p data-testid="about-stub">
        {locale === 'ko'
          ? 'About 페이지 — 자세한 내용은 Phase 4.3.4에서 채워집니다.'
          : 'About page — full content lands in Phase 4.3.4.'}
      </p>
    </StaticLayout>
  )
}
