import { useI18n } from '@/i18n/I18nProvider'
import { StaticLayout } from './StaticLayout'

export function TermsPage() {
  const { locale } = useI18n()
  return (
    <StaticLayout title={locale === 'ko' ? '이용약관' : 'Terms of Use'}>
      <p data-testid="terms-stub">
        {locale === 'ko'
          ? '이용약관 — Phase 4.3.4에서 본문이 채워집니다.'
          : 'Terms of use — full content lands in Phase 4.3.4.'}
      </p>
    </StaticLayout>
  )
}
