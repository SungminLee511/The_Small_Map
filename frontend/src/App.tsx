import { useEffect, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MapView } from '@/features/map/MapView'
import { ProfilePage } from '@/features/profile/ProfilePage'
import { AboutPage } from '@/features/static/AboutPage'
import { PrivacyPage } from '@/features/static/PrivacyPage'
import { TermsPage } from '@/features/static/TermsPage'
import { I18nProvider } from '@/i18n/I18nProvider'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

/** Bare-bones path switch: map at "/", profile at "/me", static pages
 *  at /about, /privacy, /terms. */
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
  let page: React.ReactNode
  switch (path) {
    case '/me':
      page = <ProfilePage />
      break
    case '/about':
      page = <AboutPage />
      break
    case '/privacy':
      page = <PrivacyPage />
      break
    case '/terms':
      page = <TermsPage />
      break
    default:
      page = <MapView />
  }
  return (
    <I18nProvider>
      <QueryClientProvider client={queryClient}>{page}</QueryClientProvider>
    </I18nProvider>
  )
}

export default App
