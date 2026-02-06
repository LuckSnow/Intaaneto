export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const ROLES = {
  STUDENT: 'student',
  TEACHER: 'teacher',
  ADMIN: 'admin',
}

export const DIFFICULTY_LEVELS = {
  BEGINNER: 'beginner',
  INTERMEDIATE: 'intermediate',
  ADVANCED: 'advanced',
}

export const LESSON_TYPES = {
  VIDEO: 'video',
  TEXT: 'text',
  INTERACTIVE: 'interactive',
  QUIZ: 'quiz',
}
