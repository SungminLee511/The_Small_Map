import { useCallback, useState } from 'react'

export interface GeoSample {
  lat: number
  lng: number
  accuracy_m: number
  timestamp: number
}

export interface GeoState {
  status: 'idle' | 'pending' | 'ready' | 'error'
  sample: GeoSample | null
  error: string | null
}

const HIGH_ACC_OPTS: PositionOptions = {
  enableHighAccuracy: true,
  timeout: 15_000,
  maximumAge: 0,
}

/** Wrap navigator.geolocation in a one-shot Promise + React state. */
export function useGeolocation() {
  const [state, setState] = useState<GeoState>({
    status: 'idle',
    sample: null,
    error: null,
  })

  const acquire = useCallback(async (): Promise<GeoSample> => {
    setState({ status: 'pending', sample: null, error: null })
    return new Promise((resolve, reject) => {
      if (!('geolocation' in navigator)) {
        const msg = 'Geolocation not supported by this browser'
        setState({ status: 'error', sample: null, error: msg })
        reject(new Error(msg))
        return
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const sample: GeoSample = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            accuracy_m: pos.coords.accuracy ?? 9999,
            timestamp: pos.timestamp,
          }
          setState({ status: 'ready', sample, error: null })
          resolve(sample)
        },
        (err) => {
          const msg = err.message || 'geolocation failed'
          setState({ status: 'error', sample: null, error: msg })
          reject(new Error(msg))
        },
        HIGH_ACC_OPTS,
      )
    })
  }, [])

  return { state, acquire }
}
