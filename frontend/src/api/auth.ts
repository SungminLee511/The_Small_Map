import { apiClient } from './client'
import type { UserMe } from '@/types/user'

/** Returns the absolute URL the browser should hit to start Kakao OAuth. */
export function kakaoAuthorizeUrl(): string {
  const base =
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  return `${base}/auth/kakao/authorize`
}

/** Returns null on 401 instead of throwing — easier for the React Query hook. */
export async function fetchMe(): Promise<UserMe | null> {
  try {
    const { data } = await apiClient.get<UserMe>('/auth/me')
    return data
  } catch (err) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 401) return null
    throw err
  }
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout')
}
