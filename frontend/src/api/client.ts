import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  // Carry the HttpOnly session cookie cross-origin (frontend on
  // localhost:5173, backend on localhost:8000 in dev).
  withCredentials: true,
})

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.detail || err.message || 'Unknown error'
    console.error('[API]', message)
    return Promise.reject(err)
  },
)
