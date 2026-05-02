import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchMe, logout } from '@/api/auth'
import type { UserMe } from '@/types/user'

export const ME_QUERY_KEY = ['auth', 'me'] as const

export function useMe() {
  return useQuery<UserMe | null>({
    queryKey: ME_QUERY_KEY,
    queryFn: fetchMe,
    staleTime: 5 * 60_000,
    retry: 0,
    refetchOnWindowFocus: false,
  })
}

export function useLogout() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: logout,
    onSettled: () => {
      qc.setQueryData<UserMe | null>(ME_QUERY_KEY, null)
      qc.invalidateQueries({ queryKey: ME_QUERY_KEY })
    },
  })
}
