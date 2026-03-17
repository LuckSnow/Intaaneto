import { create } from 'zustand'
import { authService } from '../services/authService'

export const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user')) || null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

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
    localStorage.setItem('user', JSON.stringify(userData))
  },

  clearError: () => set({ error: null }),
}))
