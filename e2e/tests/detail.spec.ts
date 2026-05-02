import { test, expect } from '@playwright/test'
import { FAKE_POIS, stubBackendAndKakao } from './_fixtures'

test.describe('POI detail panel + ?poi= URL param', () => {
  test.beforeEach(async ({ page }) => {
    await stubBackendAndKakao(page)
  })

  test('opens with ?poi=<id> on load and shows POI name', async ({ page }) => {
    const poi = FAKE_POIS[0]
    await page.goto(`/?poi=${poi.id}`)
    const panel = page.getByTestId('poi-detail-panel')
    await expect(panel).toBeVisible()
    await expect(panel).toContainText(poi.name)
  })

  test('shows source attribution (KOGL Type 1)', async ({ page }) => {
    const poi = FAKE_POIS[0]
    await page.goto(`/?poi=${poi.id}`)
    await expect(page.getByTestId('poi-detail-panel')).toContainText(
      /data\.go\.kr/,
    )
  })

  test('Esc closes the panel and clears ?poi=', async ({ page }) => {
    const poi = FAKE_POIS[0]
    await page.goto(`/?poi=${poi.id}`)
    await expect(page.getByTestId('poi-detail-panel')).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(page.getByTestId('poi-detail-panel')).not.toBeVisible()
    expect(new URL(page.url()).searchParams.get('poi')).toBeNull()
  })

  test('close button closes the panel', async ({ page }) => {
    const poi = FAKE_POIS[0]
    await page.goto(`/?poi=${poi.id}`)
    await page.getByLabel('Close detail panel').click()
    await expect(page.getByTestId('poi-detail-panel')).not.toBeVisible()
  })
})
