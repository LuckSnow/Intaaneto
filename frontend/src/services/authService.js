import api from './api'
import { getFirebaseAuthContext } from '../config/firebase'
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
    const { remember = true, ...loginCredentials } = credentials
    const response = await api.post('/auth/login/', loginCredentials)
    const { user, tokens } = response.data
    
    storeAuthSession({ user, tokens, remember })
    
    return response.data
  },

  // Login through the server-enforced teacher/admin portal
  teacherLogin: async (credentials) => {
    const response = await api.post('/auth/teacher_login/', credentials)
    const { user, tokens } = response.data

    storeAuthSession({ user, tokens })

    return response.data
  },

  // Google Sign-In via Firebase
  googleLogin: async (remember = true) => {
    const firebaseAuth = await getFirebaseAuthContext()
    if (!firebaseAuth) {
      const error = new Error('Firebase chưa được cấu hình cho Google Login')
      error.code = 'firebase/not-configured'
      throw error
    }

    // 1. Firebase popup → get Google ID token
    const result = await firebaseAuth.signInWithPopup(
      firebaseAuth.auth,
      firebaseAuth.googleProvider,
    )
    const idToken = await result.user.getIdToken()

    // 2. Send ID token to Django backend for verification
    const response = await api.post('/auth/google/', { id_token: idToken })
    const { user, tokens } = response.data

    storeAuthSession({ user, tokens, remember })

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

  teacherGoogleLogin: async () => {
    const firebaseAuth = await getFirebaseAuthContext()
    if (!firebaseAuth) {
      const error = new Error('Firebase chưa được cấu hình cho Google Login')
      error.code = 'firebase/not-configured'
      throw error
    }

    const result = await firebaseAuth.signInWithPopup(
      firebaseAuth.auth,
      firebaseAuth.googleProvider,
    )
    const idToken = await result.user.getIdToken()
    const response = await api.post('/auth/teacher_google/', { id_token: idToken })
    const { user, tokens } = response.data

    storeAuthSession({ user, tokens })
    return response.data
  },

  getDailyActivity: async () => {
    const response = await api.get('/auth/users/daily-activity/')
    return response.data
  },

  // Resend verification email
  resendVerification: async (email) => {
    const response = await api.post('/auth/resend_verification/', { email })
    return response.data
  },

  requestPasswordReset: async (email) => {
    const response = await api.post('/auth/password_reset_request/', { email })
    return response.data
  },

  confirmPasswordReset: async (resetData) => {
    const response = await api.post('/auth/password_reset_confirm/', resetData)
    return response.data
  },

  // Update profile
  updateProfile: async (userData) => {
    const response = await api.patch('/auth/users/update_profile/', userData)
    return response.data
  },

  updateAvatar: async (avatar) => {
    const formData = new FormData()
    formData.append('avatar', avatar)
    const response = await api.patch('/auth/users/update_profile/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  getTeacherApplication: async () => {
    const response = await api.get('/auth/users/teacher_application/')
    return response.data
  },

  submitTeacherApplication: async (applicationData) => {
    const response = await api.post(
      '/auth/users/teacher_application/',
      applicationData,
    )
    return response.data
  },
}
