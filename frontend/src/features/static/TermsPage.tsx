import { useI18n } from '@/i18n/I18nProvider'
import { StaticLayout } from './StaticLayout'

/**
 * Plain-language terms of use. Not legal advice — replace with the
 * lawyer-reviewed text before public launch.
 */
export function TermsPage() {
  const { locale } = useI18n()
  return (
    <StaticLayout title={locale === 'ko' ? '이용약관' : 'Terms of Use'}>
      {locale === 'ko' ? <KoreanContent /> : <EnglishContent />}
    </StaticLayout>
  )
}

function KoreanContent() {
  return (
    <>
      <p data-testid="terms-intro">
        이용약관은 정식 법률 검토 전 초안입니다.
      </p>

      <h2 className="text-base font-semibold mt-4">1. 목적</h2>
      <p>
        본 약관은 소소한 지도(이하 "서비스") 이용 조건을 안내합니다.
      </p>

      <h2 className="text-base font-semibold mt-4">2. 계정</h2>
      <p>
        카카오 OAuth로 로그인 가능합니다. 계정에서 발생한 모든 활동의
        책임은 사용자에게 있습니다. 의심되는 활동은 즉시 차단될 수
        있습니다.
      </p>

      <h2 className="text-base font-semibold mt-4">3. 사용자 콘텐츠</h2>
      <ul className="list-disc list-inside">
        <li>장소, 사진, 신고 내용은 비배타적·로열티 프리·전세계
          라이선스로 서비스에 제공됩니다.</li>
        <li>저작권을 침해하지 않는 콘텐츠만 업로드해야 합니다.</li>
        <li>운영진은 부적절한 콘텐츠를 사전 통보 없이 삭제할 수
          있습니다.</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">4. 금지 행위</h2>
      <ul className="list-disc list-inside">
        <li>스팸 / 허위 신고 / 위치 조작</li>
        <li>타인의 사생활 침해 (특히 사진)</li>
        <li>서비스의 정상적 운영을 방해하는 행위</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">5. 책임 제한</h2>
      <p>
        서비스는 "있는 그대로" 제공됩니다. 정확성을 보장하지 않으며,
        제공된 정보에 의존해 발생한 손해에 대해 책임지지 않습니다.
      </p>

      <h2 className="text-base font-semibold mt-4">6. 약관 변경</h2>
      <p>
        주요 변경은 서비스 내에서 사전에 공지합니다.
      </p>

      <h2 className="text-base font-semibold mt-4">7. 문의</h2>
      <p>
        문의:{' '}
        <a
          href="mailto:legal@smallmap.example"
          className="text-blue-600 hover:underline"
        >
          legal@smallmap.example
        </a>
      </p>
    </>
  )
}

function EnglishContent() {
  return (
    <>
      <p data-testid="terms-intro">
        This is a working draft. The lawyer-reviewed version replaces it
        before public launch.
      </p>

      <h2 className="text-base font-semibold mt-4">1. Purpose</h2>
      <p>
        These terms govern your use of The Small Map ("the Service").
      </p>

      <h2 className="text-base font-semibold mt-4">2. Accounts</h2>
      <p>
        Sign in via Kakao OAuth. You are responsible for activity on your
        account. Suspicious activity may be blocked immediately.
      </p>

      <h2 className="text-base font-semibold mt-4">3. Your content</h2>
      <ul className="list-disc list-inside">
        <li>
          POIs, photos, and reports you submit are licensed to the Service
          on a non-exclusive, royalty-free, worldwide basis.
        </li>
        <li>Don't upload anything that infringes copyright.</li>
        <li>
          Moderators may remove inappropriate content without prior notice.
        </li>
      </ul>

      <h2 className="text-base font-semibold mt-4">4. Prohibited use</h2>
      <ul className="list-disc list-inside">
        <li>Spam, fake reports, location spoofing</li>
        <li>Privacy invasion of others (especially in photos)</li>
        <li>Anything that disrupts normal operation of the Service</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">5. Disclaimer</h2>
      <p>
        The Service is provided "as is". We don't guarantee accuracy and
        accept no liability for losses arising from reliance on it.
      </p>

      <h2 className="text-base font-semibold mt-4">6. Changes</h2>
      <p>
        Material changes will be announced in-app before they take effect.
      </p>

      <h2 className="text-base font-semibold mt-4">7. Contact</h2>
      <p>
        Email:{' '}
        <a
          href="mailto:legal@smallmap.example"
          className="text-blue-600 hover:underline"
        >
          legal@smallmap.example
        </a>
      </p>
    </>
  )
}
