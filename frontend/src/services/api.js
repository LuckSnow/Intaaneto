import axios from 'axios'
import {
  clearAuthSession,
  getStoredAccessToken,
  getStoredRefreshToken,
  storeRefreshedTokens,
} from '../utils/authStorage'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = getStoredAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    const publicAuthRequest = [
      '/auth/login/',
      '/auth/teacher_login/',
      '/auth/teacher_google/',
      '/auth/register/',
      '/auth/google/',
      '/auth/verify_email/',
      '/auth/resend_verification/',
      '/auth/token/refresh/',
    ].some((path) => originalRequest?.url?.includes(path))
    const refreshToken = getStoredRefreshToken()

    // Refresh only an authenticated API request, never a failed login/register.
    if (
      error.response?.status === 401
      && !originalRequest?._retry
      && !publicAuthRequest
      && refreshToken
    ) {
      originalRequest._retry = true

      try {
        const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
          refresh: refreshToken,
        })

        const { access, refresh } = response.data
        storeRefreshedTokens({ access, refresh })

        originalRequest.headers.Authorization = `Bearer ${access}`
        return api(originalRequest)
      } catch (refreshError) {
        clearAuthSession()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api
