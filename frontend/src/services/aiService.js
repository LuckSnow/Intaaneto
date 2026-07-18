import api from './api'

export const aiService = {
  // Send message to AI
  sendMessage: async (messageData) => {
    const response = await api.post('/ai/chat/send_message/', messageData)
    return response.data
  },

  // Get chat sessions
  getChatSessions: async () => {
    const response = await api.get('/ai/chat/')
    return response.data
  },

  // Get chat session messages
  getChatSession: async (sessionId) => {
    const response = await api.get(`/ai/chat/${sessionId}/`)
    return response.data
  },

  // Restore the latest authorized chat for one lesson
  getLessonChatHistory: async (lessonId) => {
    const response = await api.get('/ai/chat/history/', {
      params: { lesson_id: lessonId },
    })
    return response.data
  },

  // Explain code
  explainCode: async (codeData) => {
    const response = await api.post('/ai/chat/explain_code/', codeData)
    return response.data
  },

  // Get hint for exercise
  getHint: async (hintData) => {
    const response = await api.post('/ai/chat/get_hint/', hintData)
    return response.data
  },
}
