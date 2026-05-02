import { useI18n } from '@/i18n/I18nProvider'
import { StaticLayout } from './StaticLayout'

export function AboutPage() {
  const { locale } = useI18n()
  return (
    <StaticLayout title={locale === 'ko' ? '소개' : 'About'}>
      {locale === 'ko' ? <KoreanContent /> : <EnglishContent />}
    </StaticLayout>
  )
}

function KoreanContent() {
  return (
    <>
      <p data-testid="about-intro">
        <b>소소한 지도</b>는 우리 동네의 작은 시설 — 화장실, 쓰레기통,
        벤치, 흡연구역, 음수대 — 을 한 눈에 보여주는 커뮤니티 지도입니다.
      </p>
      <h2 className="text-base font-semibold mt-4">왜 만드나요?</h2>
      <p>
        시민이 매일 마주하는 작은 시설은 공식 지도에 잘 등장하지 않습니다.
        이 지도는 사용자가 직접 등록하고, 다른 사람이 확인하고, 문제가
        생기면 신고하는 방식으로 살아 움직이는 데이터를 만들어 갑니다.
      </p>
      <h2 className="text-base font-semibold mt-4">데이터 출처</h2>
      <ul className="list-disc list-inside">
        <li>
          공공데이터포털 (data.go.kr) — 전국공중화장실표준데이터 (KOGL Type 1)
        </li>
        <li>
          공공데이터포털 (data.go.kr) — 마포구 흡연시설 현황 (KOGL Type 1)
        </li>
        <li>지도 SDK — 카카오맵 (Kakao Maps JavaScript SDK)</li>
      </ul>
      <h2 className="text-base font-semibold mt-4">기여하기</h2>
      <p>
        새 장소 등록, 기존 장소 확인, 문제 신고 — 모두 환영합니다. 신뢰도
        시스템 (평판) 으로 양질의 기여를 우대합니다.
      </p>
      <h2 className="text-base font-semibold mt-4">문의</h2>
      <p>
        문의사항은{' '}
        <a
          href="mailto:hello@smallmap.example"
          className="text-blue-600 hover:underline"
        >
          hello@smallmap.example
        </a>{' '}
        로 보내주세요.
      </p>
    </>
  )
}

function EnglishContent() {
  return (
    <>
      <p data-testid="about-intro">
        <b>The Small Map</b> is a community map of tiny city amenities —
        public toilets, trash bins, benches, smoking areas, and water
        fountains — that rarely make it onto the big maps.
      </p>
      <h2 className="text-base font-semibold mt-4">Why?</h2>
      <p>
        The small things you use every day deserve a place too. The Small
        Map stays current because residents add new spots, others confirm
        them, and anyone can flag issues.
      </p>
      <h2 className="text-base font-semibold mt-4">Data sources</h2>
      <ul className="list-disc list-inside">
        <li>
          National Public Toilet Standard Data — data.go.kr (KOGL Type 1)
        </li>
        <li>
          Mapo-gu smoking facility list — data.go.kr (KOGL Type 1)
        </li>
        <li>Map SDK — Kakao Maps JavaScript SDK</li>
      </ul>
      <h2 className="text-base font-semibold mt-4">Contribute</h2>
      <p>
        Add new spots, confirm existing ones, or report problems. The
        reputation system rewards quality contributions.
      </p>
      <h2 className="text-base font-semibold mt-4">Contact</h2>
      <p>
        Reach out at{' '}
        <a
          href="mailto:hello@smallmap.example"
          className="text-blue-600 hover:underline"
        >
          hello@smallmap.example
        </a>
        .
      </p>
    </>
  )
}
