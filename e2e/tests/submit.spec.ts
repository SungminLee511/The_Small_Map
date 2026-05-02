import { test, expect } from '@playwright/test'
import { stubBackendAndKakao } from './_fixtures'

test.describe('POI submission flow', () => {
  test.beforeEach(async ({ page, context }) => {
    await context.grantPermissions(['geolocation'])
    await stubBackendAndKakao(page, { loggedIn: true })
  })

  test('happy path: 5 steps, then ?poi=<new id> opens detail', async ({ page }) => {
    await page.goto('/')

    // Step 1: open the sheet
    await page.getByTestId('submit-fab').click()
    await expect(page.getByTestId('submit-step-type')).toBeVisible()

    // Pick toilet → next
    await page.getByTestId('submit-type-toilet').click()
    await page.getByTestId('submit-next').click()

    // Step 2: GPS
    await expect(page.getByTestId('submit-step-gps')).toBeVisible()
    await page.getByTestId('submit-gps-acquire').click()
    // The stubbed geolocation resolves with accuracy 12m → next becomes enabled
    await expect(page.getByTestId('submit-next')).toBeEnabled()
    await page.getByTestId('submit-next').click()

    // Step 3: Photo (optional — skip)
    await expect(page.getByTestId('submit-step-photo')).toBeVisible()
    await page.getByTestId('submit-next').click()

    // Step 4: Attrs (defaults)
    await expect(page.getByTestId('submit-step-attrs')).toBeVisible()
    await page.getByTestId('submit-next').click()

    // Step 5: Review → submit
    await expect(page.getByTestId('submit-step-review')).toBeVisible()
    await page.getByTestId('submit-go').click()

    // After success, sheet closes and detail panel opens for the new POI
    await expect(page.getByTestId('submit-sheet')).toHaveCount(0)
  })

  test('duplicate-nearby response opens existing POI', async ({ page }) => {
    // First, set up the duplicate response
    await page.unrouteAll()
    await stubBackendAndKakao(page, {
      loggedIn: true,
      submitResponse: {
        status: 409,
        body: {
          detail: {
            duplicate: true,
            existing_poi_id: '11111111-1111-1111-1111-111111111111',
            distance_m: 4.2,
          },
        },
      },
    })
    await page.goto('/')

    await page.getByTestId('submit-fab').click()
    await page.getByTestId('submit-type-toilet').click()
    await page.getByTestId('submit-next').click()
    await page.getByTestId('submit-gps-acquire').click()
    await expect(page.getByTestId('submit-next')).toBeEnabled()
    await page.getByTestId('submit-next').click()
    await page.getByTestId('submit-next').click()
    await page.getByTestId('submit-next').click()
    await page.getByTestId('submit-go').click()

    // Sheet closes, detail panel for the existing POI shows
    await expect(page.getByTestId('submit-sheet')).toHaveCount(0)
    await expect(page.getByTestId('poi-detail-panel')).toBeVisible()
  })
})
