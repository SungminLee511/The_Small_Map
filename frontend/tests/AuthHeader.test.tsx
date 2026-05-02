import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthHeader } from '@/features/auth/AuthHeader'
import type { UserMe } from '@/types/user'

vi.mock('@/api/auth', async () => {
  const actual = await vi.importActual<typeof import('@/api/auth')>(
    '@/api/auth',
  )
  return {
    ...actual,
    fetchMe: vi.fn(),
    logout: vi.fn(),
  }
})

import { fetchMe, logout } from '@/api/auth'

function renderWithQuery(ui: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>)
}

const ME: UserMe = {
  id: '11111111-1111-1111-1111-111111111111',
  display_name: 'Sungmin',
  email: null,
  avatar_url: null,
  is_admin: false,
  reputation: 7,
}

describe('AuthHeader', () => {
  beforeEach(() => {
    vi.mocked(fetchMe).mockReset()
    vi.mocked(logout).mockReset()
  })

  it('renders Kakao login link when logged out', async () => {
    vi.mocked(fetchMe).mockResolvedValue(null)
    renderWithQuery(<AuthHeader />)
    expect(await screen.findByTestId('auth-login-button')).toBeInTheDocument()
    expect(screen.getByTestId('auth-login-button').getAttribute('href')).toMatch(
      /\/auth\/kakao\/authorize$/,
    )
  })

  it('renders user name + reputation when logged in', async () => {
    vi.mocked(fetchMe).mockResolvedValue(ME)
    renderWithQuery(<AuthHeader />)
    expect(await screen.findByTestId('auth-user-name')).toHaveTextContent(
      'Sungmin',
    )
    expect(screen.getByText(/⭐ 7/)).toBeInTheDocument()
  })

  it('logout button calls logout mutation', async () => {
    vi.mocked(fetchMe).mockResolvedValue(ME)
    vi.mocked(logout).mockResolvedValue(undefined)
    renderWithQuery(<AuthHeader />)
    await waitFor(() => screen.getByTestId('auth-logout-button'))
    fireEvent.click(screen.getByTestId('auth-logout-button'))
    await waitFor(() => expect(logout).toHaveBeenCalled())
  })
})
