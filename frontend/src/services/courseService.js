import api from './api'

export const courseService = {
  // Get all courses
  getCourses: async (params = {}) => {
    const response = await api.get('/courses/', { params })
    return response.data
  },

  // Get course by ID
  getCourse: async (id) => {
    const response = await api.get(`/courses/${id}/`)
    return response.data
  },

  // Enroll in course
  enrollCourse: async (courseId) => {
    const response = await api.post(`/courses/${courseId}/enroll/`)
    return response.data
  },

  // Get user's enrollments
  getMyEnrollments: async () => {
    const response = await api.get('/courses/enrollments/')
    return response.data
  },

  // Get course progress
  getCourseProgress: async (courseId) => {
    const response = await api.get(`/courses/${courseId}/progress/`)
    return response.data
  },

  // Complete lesson
  completeLesson: async (lessonId) => {
    const response = await api.post(`/courses/lessons/${lessonId}/complete/`)
    return response.data
  },

  // Submit review
  submitReview: async (reviewData) => {
    const response = await api.post('/courses/reviews/', reviewData)
    return response.data
  },
}
