import { test, expect } from '@playwright/test'
import { stubBackendAndKakao } from './_fixtures'

test.describe('Auth header', () => {
  test('shows Kakao login button when logged out', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: false })
    await page.goto('/')
    await expect(page.getByTestId('auth-login-button')).toBeVisible()
    const href = await page
      .getByTestId('auth-login-button')
      .getAttribute('href')
    expect(href).toContain('/auth/kakao/authorize')
  })

  test('shows display name + reputation when logged in', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: true })
    await page.goto('/')
    await expect(page.getByTestId('auth-user-name')).toHaveText('Sungmin')
    await expect(page.getByText('⭐ 5')).toBeVisible()
  })

  test('FAB appears only when logged in', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: false })
    await page.goto('/')
    await expect(page.getByTestId('submit-fab')).toHaveCount(0)

    // Same page, but mocked logged in this time
    await page.unrouteAll()
    await stubBackendAndKakao(page, { loggedIn: true })
    await page.goto('/')
    await expect(page.getByTestId('submit-fab')).toBeVisible()
  })
})
