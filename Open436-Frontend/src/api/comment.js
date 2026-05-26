/**
 * 评论/互动 API
 */
import request from './request'

export function getReplies(postId) {
  return request.get('/api/comments/replies/', { params: { post_id: postId } })
}

export function createReply(data) {
  return request.post('/api/comments/replies/', data)
}

export function toggleLike(postId) {
  return request.post(`/api/comments/posts/${postId}/like/`)
}

export function toggleFavorite(postId) {
  return request.post(`/api/comments/posts/${postId}/favorite/`)
}
