import { test, expect } from '@playwright/test'
import { stubBackendAndKakao } from './_fixtures'

test.describe('Filter UI + URL param', () => {
  test.beforeEach(async ({ page }) => {
    await stubBackendAndKakao(page)
  })

  test('FilterBar renders all five POI type pills', async ({ page }) => {
    await page.goto('/')
    for (const id of [
      'filter-toilet',
      'filter-trash_can',
      'filter-bench',
      'filter-smoking_area',
      'filter-water_fountain',
    ]) {
      await expect(page.getByTestId(id)).toBeVisible()
    }
  })

  test('?types=toilet on load reflects only toilet active', async ({
    page,
  }) => {
    await page.goto('/?types=toilet')
    await expect(page.getByTestId('filter-toilet')).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    await expect(page.getByTestId('filter-bench')).toHaveAttribute(
      'aria-pressed',
      'false',
    )
  })

  test('clicking a pill writes ?types= to the URL', async ({ page }) => {
    await page.goto('/')
    // Deselect "toilet" from the all-active default
    await page.getByTestId('filter-toilet').click()
    await expect(page).toHaveURL(/types=/)
    const url = new URL(page.url())
    const types = (url.searchParams.get('types') ?? '').split(',')
    expect(types).not.toContain('toilet')
    expect(types).toContain('bench')
  })

  test('"없음" quick toggle clears all and writes empty types', async ({
    page,
  }) => {
    await page.goto('/')
    await page.getByText('없음').click()
    await expect(page).toHaveURL(/types=/)
    expect(new URL(page.url()).searchParams.get('types')).toBe('')
  })
})
