import api from './api'

// ─── REST API calls (Django backend) ───

export const forumService = {
  // Posts
  getPosts: (params = {}) => api.get('/forum/posts/', { params }),
  getPost: (id) => api.get(`/forum/posts/${id}/`),
  createPost: (data) => {
    const formData = new FormData()
    formData.append('title', data.title)
    formData.append('content', data.content)
    formData.append('category', data.category || 'question')
    formData.append('course_id', data.course_id)
    if (data.tag_ids) {
      data.tag_ids.forEach(id => formData.append('tag_ids', id))
    }
    ;[data.image_1, data.image_2, data.image_3, data.image_4].forEach((img, i) => {
      if (img) formData.append(`image_${i + 1}`, img)
    })
    return api.post('/forum/posts/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  updatePost: (id, data) => api.patch(`/forum/posts/${id}/`, data),
  deletePost: (id) => api.delete(`/forum/posts/${id}/`),

  // Post actions
  reactToPost: (id, reactionType) => api.post(`/forum/posts/${id}/react/`, { reaction_type: reactionType }),
  markSolved: (id) => api.post(`/forum/posts/${id}/mark_solved/`),
  reportPost: (id, data) => api.post(`/forum/posts/${id}/report/`, data),
  pinPost: (id) => api.post(`/forum/posts/${id}/pin/`),
  closePost: (id) => api.post(`/forum/posts/${id}/close/`),

  // Comments
  getComments: (postId) => api.get('/forum/comments/', { params: { post: postId } }),
  createComment: (data) => {
    const formData = new FormData()
    formData.append('post', data.post)
    formData.append('content', data.content)
    if (data.parent) formData.append('parent', data.parent)
    if (data.image) formData.append('image', data.image)
    return api.post('/forum/comments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteComment: (id) => api.delete(`/forum/comments/${id}/`),
  reactToComment: (id, reactionType) => api.post(`/forum/comments/${id}/react/`, { reaction_type: reactionType }),
  markSolution: (id) => api.post(`/forum/comments/${id}/mark_solution/`),
  reportComment: (id, data) => api.post(`/forum/comments/${id}/report/`, data),
  getReplies: (id) => api.get(`/forum/comments/${id}/replies/`),

  // Tags
  getTags: () => api.get('/forum/tags/'),

  // Follow
  toggleFollow: (userId) => api.post('/forum/follows/toggle/', { user_id: userId }),
  checkFollow: (userId) => api.get('/forum/follows/check/', { params: { user_id: userId } }),
  getMyFollowing: () => api.get('/forum/follows/my_following/'),
  getMyFollowers: () => api.get('/forum/follows/my_followers/'),
}
