import { test, expect } from '@playwright/test'
import { stubBackendAndKakao } from './_fixtures'

test.describe('Profile page (/me)', () => {
  test('shows login link when logged out', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: false })
    await page.goto('/me')
    await expect(page.getByTestId('profile-login-link')).toBeVisible()
  })

  test('shows submissions + confirmations when logged in', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: true })

    // Mock /me/submissions and /me/confirmations
    await page.route('**/api/v1/me/submissions**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
            poi_type: 'toilet',
            location: { lat: 37.55, lng: 126.92 },
            name: '내가 만든 화장실',
            attributes: {},
            source: 'user:aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            status: 'active',
            verification_status: 'unverified',
            external_id: null,
            last_verified_at: null,
            verification_count: 1,
            created_at: '2026-04-30T00:00:00Z',
            updated_at: '2026-04-30T00:00:00Z',
          },
        ]),
      })
    })
    await page.route('**/api/v1/me/confirmations**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: '[]',
      })
    })

    await page.goto('/me')
    await expect(page.getByTestId('profile-page')).toBeVisible()
    await expect(page.getByTestId('profile-reputation')).toContainText('5')
    await expect(page.getByText('내가 만든 화장실')).toBeVisible()
    await expect(page.getByText('미확인')).toBeVisible()
  })
})
