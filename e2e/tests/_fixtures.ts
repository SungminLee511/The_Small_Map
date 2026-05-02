import type { Page } from '@playwright/test'

const API_BASE = '**/api/v1'

export const FAKE_POIS = [
  {
    id: '11111111-1111-1111-1111-111111111111',
    poi_type: 'toilet',
    location: { lat: 37.5535, lng: 126.9215 },
    name: 'Mock Toilet',
    attributes: { accessibility: true, gender: 'separate', is_free: true },
    source: 'seoul.public_toilets',
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-04-30T00:00:00Z',
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    poi_type: 'bench',
    location: { lat: 37.5540, lng: 126.9220 },
    name: 'Mock Bench',
    attributes: { has_back: true },
    source: 'seed',
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-04-30T00:00:00Z',
  },
] as const

const FAKE_DETAILS: Record<string, unknown> = Object.fromEntries(
  FAKE_POIS.map((p) => [
    p.id,
    {
      ...p,
      external_id: `EXT-${p.id.slice(0, 4)}`,
      last_verified_at: '2026-04-30T00:00:00Z',
      verification_count: 2,
    },
  ]),
)

/**
 * Stub the backend API and the Kakao Maps SDK so the frontend can render
 * fully in a sandboxed e2e environment without external dependencies.
 *
 * The Kakao stub is intentionally minimal — enough for ``useKakaoLoader``
 * (from react-kakao-maps-sdk) to resolve loading=false. It does NOT
 * implement a real Map; for marker-rendering assertions we rely on
 * CustomOverlayMap children which the SDK proxies to children directly.
 */
export async function stubBackendAndKakao(page: Page): Promise<void> {
  await page.route(`${API_BASE}/pois?**`, async (route) => {
    const url = new URL(route.request().url())
    const typeParams = url.searchParams.getAll('type')
    let items: unknown[] = [...FAKE_POIS]
    if (typeParams.length > 0) {
      items = items.filter((p) =>
        typeParams.includes((p as { poi_type: string }).poi_type),
      )
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items, truncated: false }),
    })
  })

  await page.route(`${API_BASE}/pois/*`, async (route) => {
    const id = route.request().url().split('/').pop() ?? ''
    const detail = FAKE_DETAILS[id]
    if (!detail) {
      await route.fulfill({ status: 404, body: '{"detail":"not found"}' })
      return
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(detail),
    })
  })

  // Minimal Kakao Maps SDK stub — defined before the app boots.
  await page.addInitScript(() => {
    type LL = { lat: number; lng: number }
    const stub = {
      maps: {
        // react-kakao-maps-sdk calls ``kakao.maps.load(cb)`` to defer init.
        load: (cb: () => void) => cb(),
        LatLng: function (lat: number, lng: number) {
          return {
            lat,
            lng,
            getLat: () => lat,
            getLng: () => lng,
          }
        },
        LatLngBounds: function () {
          const sw = { getLat: () => 37.5, getLng: () => 126.9 }
          const ne = { getLat: () => 37.6, getLng: () => 127.0 }
          return {
            getSouthWest: () => sw,
            getNorthEast: () => ne,
            extend: () => {},
          }
        },
        Map: function (
          _container: HTMLElement,
          options: { center: LL; level: number },
        ) {
          let level = options.level
          let center = options.center
          return {
            setLevel: (l: number) => {
              level = l
            },
            getLevel: () => level,
            setCenter: (c: LL) => {
              center = c
            },
            getCenter: () => center,
            getBounds: () => ({
              getSouthWest: () => ({
                getLat: () => 37.0,
                getLng: () => 126.5,
              }),
              getNorthEast: () => ({
                getLat: () => 38.0,
                getLng: () => 127.5,
              }),
            }),
            relayout: () => {},
            setBounds: () => {},
          }
        },
        Marker: function () {
          return { setMap: () => {}, setPosition: () => {} }
        },
        CustomOverlay: function () {
          return { setMap: () => {}, setPosition: () => {} }
        },
        event: {
          addListener: () => {},
          removeListener: () => {},
        },
        services: {},
      },
    }
    // @ts-expect-error inject global
    window.kakao = stub
    // react-kakao-maps-sdk also looks for the script tag — fake "loaded" event
    setTimeout(() => {
      window.dispatchEvent(new Event('load'))
    }, 0)
  })
}
