import { useEffect, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MapView } from '@/features/map/MapView'
import { ProfilePage } from '@/features/profile/ProfilePage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

/** Bare-bones path switch: full app at "/", profile at "/me". */
function useRoute(): string {
  const [path, setPath] = useState(
    typeof window !== 'undefined' ? window.location.pathname : '/',
  )
  useEffect(() => {
    const onPop = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])
  return path
}

function App() {
  const path = useRoute()
  return (
    <QueryClientProvider client={queryClient}>
      {path === '/me' ? <ProfilePage /> : <MapView />}
    </QueryClientProvider>
  )
}

export default App
