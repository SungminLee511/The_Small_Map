import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { I18nProvider, useI18n, useT } from '@/i18n/I18nProvider'
import { LanguageToggle } from '@/i18n/LanguageToggle'

function Probe() {
  const t = useT()
  const { locale } = useI18n()
  return (
    <div>
      <span data-testid="probe-locale">{locale}</span>
      <span data-testid="probe-login">{t('auth.loginKakao')}</span>
      <span data-testid="probe-missing">{t('not.a.key' as never)}</span>
      <LanguageToggle />
    </div>
  )
}

describe('i18n', () => {
  beforeEach(() => {
    window.localStorage.clear()
    Object.defineProperty(navigator, 'language', {
      value: 'ko-KR',
      configurable: true,
    })
  })

  it('defaults to Korean when navigator.language is ko', () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )
    expect(screen.getByTestId('probe-locale').textContent).toBe('ko')
    expect(screen.getByTestId('probe-login').textContent).toBe(
      '카카오로 로그인',
    )
  })

  it('falls back to English when navigator.language is en', () => {
    Object.defineProperty(navigator, 'language', {
      value: 'en-US',
      configurable: true,
    })
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )
    expect(screen.getByTestId('probe-locale').textContent).toBe('en')
    expect(screen.getByTestId('probe-login').textContent).toBe(
      'Sign in with Kakao',
    )
  })

  it('toggle switches locale and persists in localStorage', () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )
    fireEvent.click(screen.getByTestId('language-en'))
    expect(screen.getByTestId('probe-locale').textContent).toBe('en')
    expect(window.localStorage.getItem('smallmap.locale')).toBe('en')
  })

  it('reads stored locale on mount', () => {
    window.localStorage.setItem('smallmap.locale', 'en')
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )
    expect(screen.getByTestId('probe-locale').textContent).toBe('en')
  })

  it('returns the key itself when no message exists', () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )
    expect(screen.getByTestId('probe-missing').textContent).toBe('not.a.key')
  })
})
