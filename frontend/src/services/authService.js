import api from './api'
import { signInWithPopup } from 'firebase/auth'
import { auth, googleProvider } from '../config/firebase'

export const authService = {
  // Register new user
  register: async (userData) => {
    const response = await api.post('/auth/register/', userData)
    return response.data
  },

  // Login user
  login: async (credentials) => {
    const response = await api.post('/auth/login/', credentials)
    const { user, tokens } = response.data
    
    // Store tokens
    localStorage.setItem('access_token', tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    localStorage.setItem('user', JSON.stringify(user))
    
    return response.data
  },

  // Google Sign-In via Firebase
  googleLogin: async () => {
    // 1. Firebase popup → get Google ID token
    const result = await signInWithPopup(auth, googleProvider)
    const idToken = await result.user.getIdToken()

    // 2. Send ID token to Django backend for verification
    const response = await api.post('/auth/google/', { id_token: idToken })
    const { user, tokens } = response.data

    // 3. Store tokens locally
    localStorage.setItem('access_token', tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    localStorage.setItem('user', JSON.stringify(user))

    return response.data
  },

  // Logout user
  logout: async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      await api.post('/auth/logout/', { refresh_token: refreshToken })
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }
  },

  // Get current user
  getCurrentUser: async () => {
    const response = await api.get('/auth/users/me/')
    return response.data
  },

  // Update profile
  updateProfile: async (userData) => {
    const response = await api.put('/auth/users/update_profile/', userData)
    return response.data
  },
}
