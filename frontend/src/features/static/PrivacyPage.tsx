import { useI18n } from '@/i18n/I18nProvider'
import { StaticLayout } from './StaticLayout'

export function PrivacyPage() {
  const { locale } = useI18n()
  return (
    <StaticLayout
      title={locale === 'ko' ? '개인정보처리방침' : 'Privacy Policy'}
    >
      <p data-testid="privacy-stub">
        {locale === 'ko'
          ? '개인정보 처리방침 — Phase 4.3.4에서 본문이 채워집니다.'
          : 'Privacy policy — full content lands in Phase 4.3.4.'}
      </p>
    </StaticLayout>
  )
}
