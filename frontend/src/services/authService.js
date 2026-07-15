import api from './api'
import { signInWithPopup } from 'firebase/auth'
import { auth, googleProvider } from '../config/firebase'
import {
  clearAuthSession,
  getStoredRefreshToken,
  storeAuthSession,
} from '../utils/authStorage'

export const authService = {
  // Register new user (no auto-login, requires email verification)
  register: async (userData) => {
    const response = await api.post('/auth/register/', userData)
    return response.data
  },

  // Login user
  login: async (credentials) => {
    const response = await api.post('/auth/login/', credentials)
    const { user, tokens } = response.data
    
    storeAuthSession({ user, tokens })
    
    return response.data
  },

  // Google Sign-In via Firebase
  googleLogin: async () => {
    if (!auth || !googleProvider) {
      const error = new Error('Firebase chưa được cấu hình cho Google Login')
      error.code = 'firebase/not-configured'
      throw error
    }

    // 1. Firebase popup → get Google ID token
    const result = await signInWithPopup(auth, googleProvider)
    const idToken = await result.user.getIdToken()

    // 2. Send ID token to Django backend for verification
    const response = await api.post('/auth/google/', { id_token: idToken })
    const { user, tokens } = response.data

    storeAuthSession({ user, tokens })

    return response.data
  },

  // Logout user
  logout: async () => {
    try {
      const refreshToken = getStoredRefreshToken()
      if (refreshToken) {
        await api.post('/auth/logout/', { refresh_token: refreshToken })
      }
    } finally {
      clearAuthSession()
    }
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await api.get('/auth/users/me/')
    return response.data
  },

  // Resend verification email
  resendVerification: async (email) => {
    const response = await api.post('/auth/resend_verification/', { email })
    return response.data
  },

  // Update profile
  updateProfile: async (userData) => {
    const response = await api.put('/auth/users/update_profile/', userData)
    return response.data
  },
}
