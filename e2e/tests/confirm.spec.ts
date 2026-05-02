import { test, expect } from '@playwright/test'
import { FAKE_POIS, stubBackendAndKakao } from './_fixtures'

test.describe('POI confirmation flow', () => {
  test('confirm button hidden when logged out', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: false })
    const poi = FAKE_POIS[0]
    await page.goto(`/?poi=${poi.id}`)
    await expect(page.getByTestId('poi-detail-panel')).toBeVisible()
    await expect(page.getByTestId('confirm-poi-button')).toHaveCount(0)
  })

  test('confirm button visible for unverified, fires mutation', async ({ page }) => {
    // Override the detail to unverified so the button shows up
    await stubBackendAndKakao(page, {
      loggedIn: true,
      confirmResponse: {
        status: 200,
        body: {
          poi_id: '11111111-1111-1111-1111-111111111111',
          verification_count: 2,
          verification_status: 'unverified',
          flipped_to_verified: false,
        },
      },
    })
    // Override /pois/<id> to return unverified
    await page.route('**/api/v1/pois/11111111-1111-1111-1111-111111111111', async (route) => {
      if (route.request().method() !== 'GET') {
        await route.continue()
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          ...FAKE_POIS[0],
          external_id: null,
          last_verified_at: null,
          verification_count: 1,
          verification_status: 'unverified',
          source: 'user:bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
        }),
      })
    })

    await page.goto('/?poi=11111111-1111-1111-1111-111111111111')
    await expect(page.getByTestId('poi-unverified-badge')).toBeVisible()
    const btn = page.getByTestId('confirm-poi-button')
    await expect(btn).toBeVisible()
    await btn.click()
    // After success, button text flips
    await expect(btn).toHaveText(/확인됨!/)
  })

  test('confirm button hidden on verified POIs', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: true })
    // FAKE_POIS[0] detail has no verification_status — defaults to verified
    await page.goto(`/?poi=${FAKE_POIS[0].id}`)
    await expect(page.getByTestId('poi-detail-panel')).toBeVisible()
    await expect(page.getByTestId('confirm-poi-button')).toHaveCount(0)
  })
})
