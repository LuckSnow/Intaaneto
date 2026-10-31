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
    const response = await api.post('/courses/', payload, payload instanceof FormData
      ? { headers: { 'Content-Type': 'multipart/form-data' } } : undefined)
    return response.data
  },

  updateCourse: async (courseId, payload) => {
    const response = await api.patch(`/courses/${courseId}/`, payload, payload instanceof FormData
      ? { headers: { 'Content-Type': 'multipart/form-data' } } : undefined)
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

  getLessonPdfBlob: async (lessonId) => {
    const response = await api.get(
      `/courses/lessons/${lessonId}/pdf/`,
      { responseType: 'blob' },
    )
    return response.data
  },

  // Check lesson AI processing status
  getLessonStatus: async (id) => {
    const response = await api.get(`/courses/lessons/${id}/processing_status/`)
    return response.data
  },

  getIngestionStatuses: async (courseId) => {
    const response = await api.get('/courses/lessons/ingestion-statuses/', {
      params: { course: courseId },
    })
    return response.data.results || []
  },

  getLessonAuthoringStatus: async (lessonId) => {
    const response = await api.get(`/courses/lessons/${lessonId}/authoring-status/`)
    return response.data
  },

  generateLessonSummary: async (lessonId) => {
    const response = await api.post(`/courses/lessons/${lessonId}/generate-summary/`)
    return response.data
  },

  approveLessonSummary: async (lessonId, text) => {
    const response = await api.post(`/courses/lessons/${lessonId}/approve-summary/`, { text })
    return response.data
  },

  generateLessonVideoScript: async (lessonId) => {
    const response = await api.post(`/courses/lessons/${lessonId}/generate-video-script/`)
    return response.data
  },

  approveLessonVideoScript: async (lessonId, text) => {
    const response = await api.post(
      `/courses/lessons/${lessonId}/approve-video-script/`,
      { text },
    )
    return response.data
  },

  generateLessonAssessment: async (lessonId, questionCount = 'auto') => {
    const response = await api.post(
      `/courses/lessons/${lessonId}/generate-assessment/`,
      { question_count: questionCount },
    )
    return response.data
  },

  generateLessonMultimedia: async (lessonId) => {
    const response = await api.post(
      `/courses/lessons/${lessonId}/generate-multimedia/`,
    )
    return response.data
  },

  selectTutorAvatar: async (lessonId, selection) => {
    const response = await api.put(`/courses/lessons/${lessonId}/tutor-avatar/`, selection)
    return response.data
  },

  uploadTutorAvatar: async (lessonId, image, label) => {
    const form = new FormData()
    form.append('image', image)
    form.append('label', label || 'Avatar tải lên')
    const response = await api.post(`/courses/lessons/${lessonId}/tutor-avatar/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
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

  runDialogueKnowledgeCheck: async (assessmentId, questionId, answer) => {
    const response = await api.post(
      `/exercises/assessments/${assessmentId}/dialogue-check/`,
      { question_id: questionId, answer },
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
