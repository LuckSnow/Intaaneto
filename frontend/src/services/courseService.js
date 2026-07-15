import api from './api'

export const courseService = {
  // Get all courses
  getCourses: async () => {
    const response = await api.get('/courses/')
    return response.data.results || response.data
  },

  // Get single course
  getCourse: async (id) => {
    const response = await api.get(`/courses/${id}/`)
    return response.data
  },

  // Enroll in course
  enroll: async (courseId) => {
    const response = await api.post(`/courses/${courseId}/enroll/`)
    return response.data
  },

  // Get progress
  getProgress: async (courseId) => {
    const response = await api.get(`/courses/${courseId}/progress/`)
    return response.data
  },

  // Teacher: upload and index a PDF lesson
  uploadLesson: async (formData) => {
    const response = await api.post('/courses/lessons/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  // Get lesson detail (includes ai_video_url, ai_summary)
  getLesson: async (id) => {
    const response = await api.get(`/courses/lessons/${id}/`)
    return response.data
  },

  // Check lesson AI processing status
  getLessonStatus: async (id) => {
    const response = await api.get(`/courses/lessons/${id}/processing_status/`)
    return response.data
  },

  // Reprocess failed lesson
  reprocessLesson: async (id) => {
    const response = await api.post(`/courses/lessons/${id}/reprocess/`)
    return response.data
  },

  // Mark lesson as completed
  completeLesson: async (id) => {
    const response = await api.post(`/courses/lessons/${id}/complete/`)
    return response.data
  },

  // --- Comments ---
  getComments: async (lessonId) => {
    const response = await api.get(`/courses/lesson-comments/?lesson=${lessonId}`)
    return response.data.results || response.data
  },

  addComment: async (data) => {
    const response = await api.post('/courses/lesson-comments/', data)
    return response.data
  },

  deleteComment: async (id) => {
    await api.delete(`/courses/lesson-comments/${id}/`)
  },
}
