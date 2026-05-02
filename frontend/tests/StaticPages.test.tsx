import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { I18nProvider } from '@/i18n/I18nProvider'
import { AboutPage } from '@/features/static/AboutPage'
import { PrivacyPage } from '@/features/static/PrivacyPage'
import { TermsPage } from '@/features/static/TermsPage'
import { Footer } from '@/features/static/Footer'

beforeEach(() => {
  window.localStorage.clear()
  Object.defineProperty(navigator, 'language', {
    value: 'ko-KR',
    configurable: true,
  })
})

function withProvider(ui: React.ReactNode) {
  return render(<I18nProvider>{ui}</I18nProvider>)
}

describe('AboutPage', () => {
  it('renders Korean intro by default', () => {
    withProvider(<AboutPage />)
    expect(screen.getByTestId('about-intro').textContent).toContain(
      '소소한 지도',
    )
    expect(screen.getByText('데이터 출처')).toBeInTheDocument()
  })

  it('switches to English when toggled', () => {
    withProvider(<AboutPage />)
    fireEvent.click(screen.getByTestId('language-en'))
    expect(screen.getByTestId('about-intro').textContent).toContain(
      'Small Map',
    )
    expect(screen.getByText('Data sources')).toBeInTheDocument()
  })
})

describe('PrivacyPage', () => {
  it('renders PIPA-aware Korean draft', () => {
    withProvider(<PrivacyPage />)
    expect(screen.getByTestId('privacy-intro').textContent).toContain(
      'PIPA',
    )
    expect(screen.getByText('1. 수집 항목')).toBeInTheDocument()
  })

  it('flips to English headers', () => {
    withProvider(<PrivacyPage />)
    fireEvent.click(screen.getByTestId('language-en'))
    expect(screen.getByText('1. Data we collect')).toBeInTheDocument()
  })
})

describe('TermsPage', () => {
  it('renders Korean draft', () => {
    withProvider(<TermsPage />)
    expect(screen.getByTestId('terms-intro')).toBeInTheDocument()
    expect(screen.getByText('1. 목적')).toBeInTheDocument()
  })
})

describe('Footer', () => {
  it('links to all three legal pages', () => {
    withProvider(<Footer />)
    const links = screen
      .getByTestId('map-footer')
      .querySelectorAll('a')
    const hrefs = Array.from(links).map((a) => a.getAttribute('href'))
    expect(hrefs).toEqual(['/about', '/privacy', '/terms'])
  })
})
