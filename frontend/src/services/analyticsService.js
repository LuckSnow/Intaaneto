import api from './api'

export const analyticsService = {
  getProgressReport: async (params = {}) => {
    const response = await api.get('/analytics/progress_report/', { params })
    return response.data
  },
  exportCourseProgress: async (courseId) => {
    const response = await api.get('/analytics/progress-export/', {
      params: { course_id: courseId },
      responseType: 'blob',
    })
    return response.data
  },
}
