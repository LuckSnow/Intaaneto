import api from './api'
import { db } from '../config/firebase'
import {
  collection, doc, onSnapshot, setDoc, deleteDoc,
  query, orderBy, serverTimestamp, updateDoc, increment,
} from 'firebase/firestore'

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

// ─── Firestore Realtime helpers ───

/**
 * Sync reactions from Firestore in realtime for a specific post.
 * Firestore collection: forum_posts/{postId}/reactions
 */
export function subscribeToPostReactions(postId, callback) {
  const ref = collection(db, 'forum_posts', String(postId), 'reactions')
  const q = query(ref, orderBy('createdAt', 'desc'))
  return onSnapshot(q, (snapshot) => {
    const reactions = snapshot.docs.map(d => ({ id: d.id, ...d.data() }))
    callback(reactions)
  })
}

export function subscribeToComments(postId, callback) {
  const ref = collection(db, 'forum_posts', String(postId), 'comments')
  const q = query(ref, orderBy('createdAt', 'asc'))
  return onSnapshot(q, (snapshot) => {
    const comments = snapshot.docs.map(d => ({ id: d.id, ...d.data() }))
    callback(comments)
  })
}

/**
 * Write a lightweight reaction doc to Firestore for realtime sync.
 * The real reaction is also persisted via REST API (Django).
 */
export async function writeRealtimeReaction(postId, userId, userName, reactionType) {
  const docRef = doc(db, 'forum_posts', String(postId), 'reactions', String(userId))
  if (!reactionType) {
    await deleteDoc(docRef)
    return
  }
  await setDoc(docRef, {
    userId,
    userName,
    reactionType,
    createdAt: serverTimestamp(),
  })
}

export async function writeRealtimeComment(postId, commentData) {
  const docRef = doc(
    db, 'forum_posts', String(postId), 'comments', String(commentData.id)
  )
  await setDoc(docRef, {
    ...commentData,
    createdAt: serverTimestamp(),
  })
}

export async function deleteRealtimeComment(postId, commentId) {
  const docRef = doc(db, 'forum_posts', String(postId), 'comments', String(commentId))
  await deleteDoc(docRef)
}
