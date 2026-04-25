import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MapView } from '@/features/map/MapView'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MapView />
    </QueryClientProvider>
  )
}

export default App
