import { test, expect } from '@playwright/test'
import { FAKE_POIS, stubBackendAndKakao } from './_fixtures'

test.describe('Report submission flow', () => {
  test('logged-out users do not see "신고하기"', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: false })
    await page.goto(`/?poi=${FAKE_POIS[0].id}`)
    await expect(page.getByTestId('poi-detail-panel')).toBeVisible()
    await expect(
      page.getByTestId('open-report-modal-button'),
    ).toHaveCount(0)
  })

  test('opens modal, submits, then sheet closes', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: true })
    await page.goto(`/?poi=${FAKE_POIS[0].id}`)
    await page.getByTestId('open-report-modal-button').click()
    await expect(page.getByTestId('report-submit-modal')).toBeVisible()
    await page.getByTestId('report-type-dirty').click()
    await page.getByTestId('report-description').fill('급함')
    await page.getByTestId('report-submit-button').click()
    await expect(page.getByTestId('report-submit-modal')).toHaveCount(0)
  })

  test('submit disabled until a type is picked', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: true })
    await page.goto(`/?poi=${FAKE_POIS[0].id}`)
    await page.getByTestId('open-report-modal-button').click()
    await expect(page.getByTestId('report-submit-button')).toBeDisabled()
    await page.getByTestId('report-type-out_of_order').click()
    await expect(page.getByTestId('report-submit-button')).toBeEnabled()
  })
})

test.describe('Notifications bell', () => {
  test('renders nothing when logged out', async ({ page }) => {
    await stubBackendAndKakao(page, { loggedIn: false })
    await page.goto('/')
    await expect(page.getByTestId('notifications-bell')).toHaveCount(0)
  })

  test('shows unread badge and lists items on open', async ({ page }) => {
    await stubBackendAndKakao(page, {
      loggedIn: true,
      notifications: {
        unread: 1,
        list: [
          {
            id: 'n-1',
            type: 'report_resolved',
            payload: { poi_id: FAKE_POIS[0].id, report_id: 'r-1' },
            read_at: null,
            created_at: new Date().toISOString(),
          },
        ],
      },
    })
    await page.goto('/')
    await expect(page.getByTestId('notifications-bell')).toBeVisible()
    await expect(
      page.getByTestId('notifications-unread-badge'),
    ).toContainText('1')
    await page.getByTestId('notifications-bell').click()
    await expect(
      page.getByTestId('notifications-dropdown'),
    ).toBeVisible()
    await expect(
      page.getByText('신고가 해결되었습니다'),
    ).toBeVisible()
  })

  test('clicking a notification adds ?poi= to URL', async ({ page }) => {
    await stubBackendAndKakao(page, {
      loggedIn: true,
      notifications: {
        unread: 1,
        list: [
          {
            id: 'n-1',
            type: 'poi_verified',
            payload: { poi_id: FAKE_POIS[0].id },
            read_at: null,
            created_at: new Date().toISOString(),
          },
        ],
      },
    })
    await page.goto('/')
    await page.getByTestId('notifications-bell').click()
    await page.getByTestId('notification-item').click()
    await expect(page).toHaveURL(new RegExp(`poi=${FAKE_POIS[0].id}`))
  })
})
