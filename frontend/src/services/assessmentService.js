import api from './api'

const results = (response) => response.data.results || response.data

export const assessmentService = {
  getManagedCourses: async () => {
    const response = await api.get('/courses/managed/')
    return results(response)
  },

  getManagedLessons: async (courseId) => {
    const response = await api.get('/courses/lessons/', {
      params: { course: courseId },
    })
    return results(response)
  },

  getForLesson: async (lessonId) => {
    const response = await api.get('/exercises/assessments/', {
      params: { lesson: lessonId },
    })
    return results(response)[0] || null
  },

  create: async (payload) => {
    const response = await api.post('/exercises/assessments/', payload)
    return response.data
  },

  update: async (assessmentId, payload) => {
    const response = await api.patch(
      `/exercises/assessments/${assessmentId}/`,
      payload,
    )
    return response.data
  },

  remove: async (assessmentId) => {
    await api.delete(`/exercises/assessments/${assessmentId}/`)
  },
}
