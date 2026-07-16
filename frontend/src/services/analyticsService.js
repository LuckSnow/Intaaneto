import api from './api'

export const analyticsService = {
  getProgressReport: async (params = {}) => {
    const response = await api.get('/analytics/progress_report/', { params })
    return response.data
  },
}
