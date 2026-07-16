import api from './api'

export const courseService = {
  // Get all courses
  getCourses: async () => {
    const response = await api.get('/courses/')
    return response.data.results || response.data
  },

  // Teacher: include owned draft and published courses.
  getManagedCourses: async () => {
    const response = await api.get('/courses/managed/')
    return response.data.results || response.data
  },

  createCourse: async (payload) => {
    const response = await api.post('/courses/', payload)
    return response.data
  },

  updateCourse: async (courseId, payload) => {
    const response = await api.patch(`/courses/${courseId}/`, payload)
    return response.data
  },

  deleteCourse: async (courseId) => {
    await api.delete(`/courses/${courseId}/`)
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

  // Get the learner-safe published assessment for one enrolled lesson.
  getLessonAssessment: async (lessonId) => {
    const response = await api.get(`/exercises/assessments/?lesson=${lessonId}`)
    const assessments = response.data.results || response.data
    return assessments[0] || null
  },

  // Submit choices only; score, pass state, mastery, and progression are server-owned.
  submitAssessment: async (assessmentId, answers) => {
    const response = await api.post(`/exercises/assessments/${assessmentId}/submit/`, {
      answers,
    })
    return response.data
  },

  // Retrieve lesson-scoped evidence for objectives missed in one owned attempt.
  getAssessmentReinforcement: async (assessmentId, attemptId) => {
    const response = await api.post(
      `/exercises/assessments/${assessmentId}/reinforcement/`,
      { attempt_id: attemptId },
    )
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
