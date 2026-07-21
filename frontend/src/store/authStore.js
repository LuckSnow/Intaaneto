import { create } from 'zustand'
import { authService } from '../services/authService'
import {
  clearAuthSession,
  getStoredAccessToken,
  getStoredUser,
  storeCurrentUser,
} from '../utils/authStorage'

const hasStoredAccessToken = !!getStoredAccessToken()

export const useAuthStore = create((set) => ({
  user: getStoredUser(),
  isAuthenticated: hasStoredAccessToken,
  isInitializing: hasStoredAccessToken,
  isLoading: false,
  error: null,

  initializeAuth: async () => {
    if (!getStoredAccessToken()) {
      set({ user: null, isAuthenticated: false, isInitializing: false })
      return
    }
    try {
      const user = await authService.getCurrentUser()
      storeCurrentUser(user)
      set({ user, isAuthenticated: true, isInitializing: false })
    } catch {
      clearAuthSession()
      set({ user: null, isAuthenticated: false, isInitializing: false })
    }
  },

  googleLogin: async () => {
    set({ isLoading: true, error: null })
    try {
      const data = await authService.googleLogin()
      set({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
      })
      return data
    } catch (error) {
      set({
        error: error.response?.data?.error || 'Google login failed',
        isLoading: false,
      })
      throw error
    }
  },

  login: async (credentials) => {
    set({ isLoading: true, error: null })
    try {
      const data = await authService.login(credentials)
      set({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
      })
      return data
    } catch (error) {
      set({
        error: error.response?.data?.error || 'Login failed',
        isLoading: false,
      })
      throw error
    }
  },

  teacherLogin: async (credentials) => {
    set({ isLoading: true, error: null })
    try {
      const data = await authService.teacherLogin(credentials)
      set({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
      })
      return data
    } catch (error) {
      set({
        error: error.response?.data?.error || 'Teacher login failed',
        isLoading: false,
      })
      throw error
    }
  },

  teacherGoogleLogin: async () => {
    set({ isLoading: true, error: null })
    try {
      const data = await authService.teacherGoogleLogin()
      set({
        user: data.user,
        isAuthenticated: true,
        isLoading: false,
      })
      return data
    } catch (error) {
      set({
        error: error.response?.data?.error || 'Teacher Google login failed',
        isLoading: false,
      })
      throw error
    }
  },

  register: async (userData) => {
    set({ isLoading: true, error: null })
    try {
      const data = await authService.register(userData)
      // Don't auto-login — user needs to verify email first
      set({ isLoading: false })
      return data
    } catch (error) {
      set({
        error: error.response?.data || 'Registration failed',
        isLoading: false,
      })
      throw error
    }
  },

  logout: async () => {
    try {
      await authService.logout()
    } finally {
      set({
        user: null,
        isAuthenticated: false,
        error: null,
      })
    }
  },

  updateUser: (userData) => {
    set({ user: userData })
    storeCurrentUser(userData)
  },

  clearError: () => set({ error: null }),
}))
