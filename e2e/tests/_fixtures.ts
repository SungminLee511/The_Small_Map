import type { Page, Route } from '@playwright/test'

const API_BASE = '**/api/v1'

export const FAKE_USER = {
  id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  display_name: 'Sungmin',
  email: null,
  avatar_url: null,
  is_admin: false,
  reputation: 5,
}

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
export interface StubOptions {
  /** When true, /auth/me returns FAKE_USER. Default: false (logged out). */
  loggedIn?: boolean
  /** Response from POST /api/v1/pois (mocked submission). */
  submitResponse?: { status: number; body: Record<string, unknown> }
  /** Response from POST /api/v1/pois/{id}/confirm. */
  confirmResponse?: { status: number; body: Record<string, unknown> }
  /** Server-side photo presign mock. */
  presignResponse?: {
    upload_id: string
    upload_url: string
    fields: Record<string, string>
    expires_at: string
  }
  /** Pre-seeded notifications + unread count. */
  notifications?: {
    list?: Array<{
      id: string
      type: string
      payload: Record<string, unknown>
      read_at: string | null
      created_at: string
    }>
    unread?: number
  }
}

export async function stubBackendAndKakao(
  page: Page,
  options: StubOptions = {},
): Promise<void> {
  // /auth/me — logged in or out
  await page.route(`${API_BASE}/auth/me`, async (route) => {
    if (options.loggedIn) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(FAKE_USER),
      })
    } else {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: '{"detail":"not authenticated"}',
      })
    }
  })

  await page.route(`${API_BASE}/auth/logout`, async (route) => {
    await route.fulfill({ status: 204, body: '' })
  })

  // POST /pois (submission) — must come before the catch-all GET handler
  // because Playwright matches first-registered route last; we use the
  // request method to disambiguate.
  await page.route(`${API_BASE}/pois`, async (route: Route) => {
    if (route.request().method() === 'POST') {
      const r = options.submitResponse ?? {
        status: 201,
        body: {
          id: 'cccccccc-cccc-cccc-cccc-cccccccccccc',
          poi_type: 'toilet',
          location: { lat: 37.55, lng: 126.92 },
          name: 'Submitted',
          attributes: {},
          source: `user:${FAKE_USER.id}`,
          status: 'active',
          verification_status: 'unverified',
          external_id: null,
          last_verified_at: null,
          verification_count: 1,
          created_at: '2026-04-30T00:00:00Z',
          updated_at: '2026-04-30T00:00:00Z',
        },
      }
      await route.fulfill({
        status: r.status,
        contentType: 'application/json',
        body: JSON.stringify(r.body),
      })
      return
    }
    // Fall through to GET bbox handler
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

  // GET /pois?bbox=... (the bbox catch-all)
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

  // POST /pois/{id}/confirm
  await page.route(`${API_BASE}/pois/*/confirm`, async (route: Route) => {
    const id =
      route.request().url().match(/\/pois\/([^/]+)\/confirm/)?.[1] ?? ''
    const r = options.confirmResponse ?? {
      status: 200,
      body: {
        poi_id: id,
        verification_count: 2,
        verification_status: 'unverified',
        flipped_to_verified: false,
      },
    }
    await route.fulfill({
      status: r.status,
      contentType: 'application/json',
      body: JSON.stringify(r.body),
    })
  })

  // POST /pois/{id}/reports
  await page.route(`${API_BASE}/pois/*/reports`, async (route) => {
    if (route.request().method() === 'POST') {
      const id =
        route.request().url().match(/\/pois\/([^/]+)\/reports/)?.[1] ?? ''
      const body = route.request().postDataJSON() as {
        report_type: string
        description: string | null
      }
      const now = new Date().toISOString()
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr',
          poi_id: id,
          reporter_id: FAKE_USER.id,
          report_type: body.report_type,
          description: body.description,
          photo_url: null,
          status: 'active',
          confirmation_count: 0,
          resolved_at: null,
          resolved_by: null,
          resolution_note: null,
          expires_at: now,
          created_at: now,
          updated_at: now,
        }),
      })
      return
    }
    // GET — empty list by default
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: '{"items":[],"truncated":false}',
    })
  })

  // POST /reports/{id}/confirm | resolve | dismiss
  await page.route(`${API_BASE}/reports/*/confirm`, async (route) => {
    const id =
      route.request().url().match(/\/reports\/([^/]+)\/confirm/)?.[1] ?? ''
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ report_id: id, confirmation_count: 1 }),
    })
  })
  await page.route(`${API_BASE}/reports/*/resolve`, async (route) => {
    const id =
      route.request().url().match(/\/reports\/([^/]+)\/resolve/)?.[1] ?? ''
    const body = route.request().postDataJSON() as {
      resolution_note: string
    }
    const now = new Date().toISOString()
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id,
        poi_id: 'p-1',
        reporter_id: FAKE_USER.id,
        report_type: 'dirty',
        description: null,
        photo_url: null,
        status: 'resolved',
        confirmation_count: 0,
        resolved_at: now,
        resolved_by: FAKE_USER.id,
        resolution_note: body.resolution_note,
        expires_at: now,
        created_at: now,
        updated_at: now,
      }),
    })
  })

  // Notifications
  await page.route(`${API_BASE}/notifications/unread-count`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ unread: options.notifications?.unread ?? 0 }),
    })
  })
  await page.route(
    `${API_BASE}/notifications/read-all`,
    async (route) => await route.fulfill({ status: 204, body: '' }),
  )
  await page.route(`${API_BASE}/notifications/*/read`, async (route) => {
    const id = route.request().url().split('/').slice(-2)[0]
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id,
        type: 'report_resolved',
        payload: {},
        read_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      }),
    })
  })
  await page.route(`${API_BASE}/notifications**`, async (route) => {
    const url = new URL(route.request().url())
    if (url.pathname.endsWith('/notifications')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(options.notifications?.list ?? []),
      })
      return
    }
    await route.continue()
  })

  // Photo presign + the actual R2 PUT URL
  await page.route(`${API_BASE}/uploads/photo-presign`, async (route) => {
    const r = options.presignResponse ?? {
      upload_id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
      upload_url: 'https://stub-r2.example/upload',
      fields: { 'Content-Type': 'image/jpeg' },
      expires_at: '2026-05-02T01:00:00Z',
    }
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify(r),
    })
  })

  await page.route('https://stub-r2.example/upload', async (route) => {
    await route.fulfill({ status: 200, body: '' })
  })

  // GET /pois/{id} (detail)
  await page.route(`${API_BASE}/pois/*`, async (route) => {
    if (route.request().method() !== 'GET') {
      await route.continue()
      return
    }
    const id = route.request().url().split('/').pop()?.split('?')[0] ?? ''
    const detail = FAKE_DETAILS[id]
    if (!detail) {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: '{"detail":"not found"}',
      })
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

    // Stub navigator.geolocation so the submit-flow GPS step resolves
    // immediately with a known sample (Mapo HQ, accuracy 12m).
    Object.defineProperty(navigator, 'geolocation', {
      configurable: true,
      value: {
        getCurrentPosition: (
          ok: (pos: GeolocationPosition) => void,
        ) => {
          const fake = {
            coords: {
              latitude: 37.566535,
              longitude: 126.901320,
              accuracy: 12,
              altitude: null,
              altitudeAccuracy: null,
              heading: null,
              speed: null,
            } as GeolocationCoordinates,
            timestamp: Date.now(),
          } as GeolocationPosition
          setTimeout(() => ok(fake), 0)
        },
        watchPosition: () => 0,
        clearWatch: () => {},
      },
    })
  })
}
