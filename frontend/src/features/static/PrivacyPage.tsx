import { useI18n } from '@/i18n/I18nProvider'
import { StaticLayout } from './StaticLayout'

/**
 * Privacy policy. NOT a legal document — it's a clear, factual outline
 * of what's collected and why. PIPA-compliant baseline only; consult a
 * Korean lawyer before public launch.
 */
export function PrivacyPage() {
  const { locale } = useI18n()
  return (
    <StaticLayout
      title={locale === 'ko' ? '개인정보처리방침' : 'Privacy Policy'}
    >
      {locale === 'ko' ? <KoreanContent /> : <EnglishContent />}
    </StaticLayout>
  )
}

function KoreanContent() {
  return (
    <>
      <p data-testid="privacy-intro">
        본 페이지는 PIPA(개인정보 보호법) 기준으로 작성된 초안입니다.
        정식 법률 자문 후 보완될 예정입니다.
      </p>

      <h2 className="text-base font-semibold mt-4">1. 수집 항목</h2>
      <ul className="list-disc list-inside">
        <li>카카오 OAuth 계정 식별자, 닉네임, (선택)이메일, 프로필 사진 URL</li>
        <li>로그인 세션 쿠키 (HttpOnly, Secure)</li>
        <li>사용자가 등록한 장소의 위치, 사진, 속성</li>
        <li>제출 시 측정된 GPS 좌표 (검증 목적, 서버 저장)</li>
        <li>서버 액세스 로그 (요청 경로, 상태 코드, 응답 시간, IP)</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">2. 사용 목적</h2>
      <ul className="list-disc list-inside">
        <li>지도 표시 및 사용자 기여 검증</li>
        <li>스팸 / 어뷰즈 방지 (속도 제한, 평판 시스템)</li>
        <li>서비스 안정성 모니터링</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">3. 사진 처리 (PIPA)</h2>
      <p>
        업로드된 사진은 공개 노출 전 자동 얼굴/번호판 흐림 처리 후 저장합니다
        (보존 기간: 무기한, 사용자 또는 운영자가 삭제 시까지). 처리 전 임시
        업로드는 1시간 후 삭제됩니다.
      </p>

      <h2 className="text-base font-semibold mt-4">4. 보존 기간</h2>
      <ul className="list-disc list-inside">
        <li>계정 정보: 탈퇴 시 즉시 삭제</li>
        <li>등록한 장소: 탈퇴해도 익명화하여 유지(공공 가치)</li>
        <li>액세스 로그: 90일</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">5. 권리 및 문의</h2>
      <p>
        열람, 수정, 삭제, 처리 정지 요청은{' '}
        <a
          href="mailto:privacy@smallmap.example"
          className="text-blue-600 hover:underline"
        >
          privacy@smallmap.example
        </a>{' '}
        로 보내주세요. 사진 신고는 각 장소 상세에서 가능합니다.
      </p>
    </>
  )
}

function EnglishContent() {
  return (
    <>
      <p data-testid="privacy-intro">
        This is a working draft aligned with Korea's Personal Information
        Protection Act (PIPA). It will be replaced after legal review.
      </p>

      <h2 className="text-base font-semibold mt-4">1. Data we collect</h2>
      <ul className="list-disc list-inside">
        <li>
          Kakao OAuth account identifier, nickname, (optional) email, and
          profile photo URL
        </li>
        <li>Session cookie (HttpOnly, Secure)</li>
        <li>POIs you submit: location, photo, attributes</li>
        <li>
          GPS sample captured at submission time (used to validate the
          claimed location)
        </li>
        <li>Access logs (path, status, latency, IP)</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">2. How we use it</h2>
      <ul className="list-disc list-inside">
        <li>Render the map and verify contributions</li>
        <li>Anti-spam / anti-abuse (rate limits, reputation)</li>
        <li>Operational monitoring</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">3. Photo handling (PIPA)</h2>
      <p>
        Uploaded photos are run through automatic face / license-plate
        blurring before they become publicly visible, then stored
        indefinitely (until you or moderators delete them). Unclaimed
        uploads are deleted after 1 hour.
      </p>

      <h2 className="text-base font-semibold mt-4">4. Retention</h2>
      <ul className="list-disc list-inside">
        <li>Account data: deleted on account closure</li>
        <li>Submitted POIs: anonymized but retained (public value)</li>
        <li>Access logs: 90 days</li>
      </ul>

      <h2 className="text-base font-semibold mt-4">5. Rights & contact</h2>
      <p>
        For access / correction / deletion requests, email{' '}
        <a
          href="mailto:privacy@smallmap.example"
          className="text-blue-600 hover:underline"
        >
          privacy@smallmap.example
        </a>
        . Photos can also be reported from each POI's detail panel.
      </p>
    </>
  )
}
