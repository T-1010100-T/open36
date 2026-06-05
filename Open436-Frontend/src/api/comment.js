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

export function toggleReplyLike(replyId) {
  return request.post(`/api/comments/replies/${replyId}/like/`)
}

export function getInteractionStatus(postId) {
  return request.get(`/api/comments/posts/${postId}/interaction-status/`)
}

export function getMyFavorites(params) {
  return request.get('/api/comments/favorites/', { params })
}

// 用户关注
export function toggleFollow(userId) {
  return request.post(`/api/comments/follows/users/${userId}/toggle/`)
}

export function getFollowStatus(userId) {
  return request.get(`/api/comments/follows/users/${userId}/status/`)
}

export function getMyFollowing(params) {
  return request.get('/api/comments/follows/my-following/', { params })
}

export function getMyFollowers(params) {
  return request.get('/api/comments/follows/my-followers/', { params })
}

// 话题
export function getTopics(params) {
  return request.get('/api/comments/topics/', { params })
}

export function toggleTopicFollow(topicId) {
  return request.post(`/api/comments/topics/${topicId}/follow/`)
}

export function getTopicFollowStatus(topicId) {
  return request.get(`/api/comments/topics/${topicId}/follow-status/`)
}

export function getMyTopics() {
  return request.get('/api/comments/topics/my-topics/')
}

// 分享
export function recordShare(postId, shareType) {
  return request.post(`/api/comments/posts/${postId}/share/`, { share_type: shareType })
}

export function getShareCount(postId) {
  return request.get(`/api/comments/posts/${postId}/share-count/`)
}
