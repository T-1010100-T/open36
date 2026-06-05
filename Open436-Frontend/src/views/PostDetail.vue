<template>
  <ForumHeader />
  <AppSidebar @select="() => {}" />
  <div class="forum-layout with-sidebar">
    <div class="forum-main">
      <div v-if="!post && !loading" class="card">
        <div class="empty-state">
          <p>帖子不存在或已被删除</p>
          <p v-if="fetchError" style="color: var(--error); font-size: 12px; margin-top: var(--s-sm)">{{ fetchError }}</p>
          <p style="color: var(--text-disabled); font-size: 12px; margin-top: var(--s-xs)">ID: {{ route.params.id }}</p>
          <router-link to="/forum" class="btn btn-text" style="margin-top: var(--s-base)">返回论坛</router-link>
        </div>
      </div>
      <template v-if="post">
        <div class="card">
          <div class="post-detail">
            <div class="post-meta">
              <img :src="`https://ui-avatars.com/api/?name=${post.author}&background=1976D2&color=fff&size=40`" class="avatar" />
              <div>
                <div class="author-name">u/{{ post.author }}</div>
                <div class="post-time">{{ formatDate(post.createdAt) }} · {{ post.section }}</div>
              </div>
            </div>
            <h1 class="post-title">{{ post.title }}</h1>
            <div class="post-content" v-html="postHtml"></div>
            <div class="post-actions">
              <button v-if="auth.canPost" class="action-btn" :class="{ active: liked }" :disabled="actionLoading.like" @click="handleLike">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                {{ post.votes }}
              </button>
              <button v-if="auth.canPost" class="action-btn" :class="{ active: favorited }" :disabled="actionLoading.favorite" @click="handleFavorite">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
                {{ favorited ? '已收藏' : '收藏' }}
              </button>
              <button class="action-btn" @click="shareRef.open(null, post?.id)">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
                分享
              </button>
              <span v-if="!auth.canPost" class="guest-tip">登录后可互动</span>
            </div>
          </div>
        </div>
        <div class="card" style="margin-top: var(--s-base)">
          <div class="card-header">评论 ({{ flatComments.length }})</div>
          <div v-if="auth.canPost" class="comment-form">
            <div v-if="replyTo" class="reply-to-bar">
              回复 #{{ replyTo.floor }} {{ replyTo.author }}
              <button class="cancel-reply" @click="cancelReply">取消</button>
            </div>
            <textarea v-model="newComment" class="form-textarea" :placeholder="replyTo ? `回复 #${replyTo.floor}...` : '写下你的评论...'" rows="3"></textarea>
            <button class="btn btn-primary btn-sm" style="margin-top: var(--s-sm)" @click="submitComment" :disabled="commentLoading">
              {{ commentLoading ? '发送中...' : (replyTo ? '回复' : '发表评论') }}
            </button>
          </div>
          <div v-else class="guest-comment-tip">
            <span>登录后可发表评论</span>
          </div>
          <div class="comments-list">
            <template v-for="c in commentTree" :key="c.id">
              <div class="comment-item">
                <div class="comment-header">
                  <img :src="`https://ui-avatars.com/api/?name=${c.author}&background=1976D2&color=fff&size=32`" class="avatar avatar-sm" />
                  <span class="comment-author">u/{{ c.author }}</span>
                  <span class="comment-floor">#{{ c.floor }}</span>
                  <span class="comment-time">{{ formatDate(c.createdAt) }}</span>
                </div>
                <div class="comment-body">{{ c.content }}</div>
                <div class="comment-actions">
                  <button v-if="auth.canPost" class="comment-action-btn" :class="{ active: c.isLiked }" @click="handleReplyLike(c)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                    {{ c.likesCount || '' }}
                  </button>
                  <button v-if="auth.canPost" class="comment-action-btn" @click="startReply(c)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    回复
                  </button>
                </div>
              </div>
              <div v-for="child in c.children" :key="child.id" class="comment-item nested">
                <div class="comment-header">
                  <img :src="`https://ui-avatars.com/api/?name=${child.author}&background=1976D2&color=fff&size=28`" class="avatar avatar-xs" />
                  <span class="comment-author">u/{{ child.author }}</span>
                  <span class="comment-time">{{ formatDate(child.createdAt) }}</span>
                  <span class="reply-indicator">回复 #{{ c.floor }}</span>
                </div>
                <div class="comment-body">{{ child.content }}</div>
                <div class="comment-actions">
                  <button v-if="auth.canPost" class="comment-action-btn" :class="{ active: child.isLiked }" @click="handleReplyLike(child)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
                    {{ child.likesCount || '' }}
                  </button>
                  <button v-if="auth.canPost" class="comment-action-btn" @click="startReply(child)">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    回复
                  </button>
                </div>
              </div>
            </template>
            <div v-if="flatComments.length === 0 && !commentLoading" class="empty-state" style="padding: var(--s-xl)">
              <p style="font-size: 13px">暂无评论，快来抢沙发吧</p>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
  <ShareModal ref="shareRef" />
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import ShareModal from '@/components/ShareModal.vue'
import { useSectionStore } from '@/stores/section'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { formatDate, markdownToHtml } from '@/utils/format'
import { getPost } from '@/api/post'
import { getReplies, createReply, toggleLike, toggleFavorite, toggleReplyLike, getInteractionStatus } from '@/api/comment'

const route = useRoute()
const sectionStore = useSectionStore()
const ui = useUIStore()
const auth = useAuthStore()
const shareRef = ref(null)
const liked = ref(false)
const favorited = ref(false)
const newComment = ref('')
const loading = ref(false)
const post = ref(null)
const fetchError = ref('')
const flatComments = ref([])
const commentTree = ref([])
const replyTo = ref(null)
const commentLoading = ref(false)
const actionLoading = ref({ like: false, favorite: false })

const postHtml = computed(() => markdownToHtml(post.value?.content || ''))

async function fetchPost(id) {
  loading.value = true
  fetchError.value = ''
  try {
    const res = await getPost(id)
    const raw = res?.data || res
    if (raw && raw.id) {
      const sec = sectionStore.getSectionById(raw.section?.section_id)
      post.value = {
        id: raw.id,
        title: raw.title || '',
        content: raw.content || '',
        author: raw.author?.nickname || `用户${raw.author?.user_id || ''}`,
        section: sec?.name || '未知板块',
        votes: raw.likes_count || 0,
        createdAt: raw.created_at
      }
      await fetchReplies(id)
      await fetchInteractionStatus(id)
    } else {
      post.value = null
    }
  } catch (e) {
    const status = e?.response?.status
    const msg = e?.response?.data?.message || e?.message || '请求失败'
    fetchError.value = `[${status || 'ERR'}] ${msg}`
    post.value = null
  } finally {
    loading.value = false
  }
}

async function fetchReplies(postId) {
  try {
    const res = await getReplies(postId)
    const data = res?.data || res || {}
    const results = data.results || []
    const mapped = results.map(r => ({
      id: r.id,
      parentId: r.parent_id,
      author: r.author?.nickname || `用户${r.author?.user_id || ''}`,
      content: r.content,
      floor: r.floor_number,
      createdAt: r.created_at,
      likesCount: r.likes_count || 0,
      isLiked: !!r.is_liked,
      children: []
    }))
    flatComments.value = mapped
    buildCommentTree(mapped)
  } catch (e) {
    console.warn('Failed to fetch replies:', e)
    flatComments.value = []
    commentTree.value = []
  }
}

function buildCommentTree(flat) {
  const map = {}
  const roots = []
  flat.forEach(c => { map[c.id] = c })
  flat.forEach(c => {
    c.children = []
    if (c.parentId && map[c.parentId]) {
      map[c.parentId].children.push(c)
    } else {
      roots.push(c)
    }
  })
  commentTree.value = roots
}

async function fetchInteractionStatus(postId) {
  try {
    const res = await getInteractionStatus(postId)
    const data = res?.data || res || {}
    liked.value = !!data.is_liked
    favorited.value = !!data.is_favorited
    if (data.likes_count !== undefined && post.value) {
      post.value.votes = data.likes_count
    }
  } catch (e) {
    console.warn('Failed to fetch interaction status:', e)
  }
}

function startReply(comment) {
  replyTo.value = { id: comment.id, floor: comment.floor, author: comment.author }
}

function cancelReply() {
  replyTo.value = null
}

async function handleReplyLike(comment) {
  if (!auth.canPost) return
  try {
    const res = await toggleReplyLike(comment.id)
    const data = res?.data || {}
    if (data.is_liked !== undefined) comment.isLiked = data.is_liked
    if (data.likes_count !== undefined) comment.likesCount = data.likes_count
  } catch (e) {
    console.warn('Reply like failed:', e)
  }
}

async function handleLike() {
  if (!auth.canPost || actionLoading.value.like) return
  actionLoading.value.like = true
  try {
    const res = await toggleLike(post.value.id)
    const data = res?.data || {}
    const msg = res?.message || ''
    if (data.is_liked !== undefined) {
      liked.value = data.is_liked
    }
    if (data.likes_count !== undefined) {
      post.value.votes = data.likes_count
    }
    ui.showToast(msg, liked.value ? 'success' : 'info')
  } catch (e) {
    const msg = e?.response?.data?.message || '操作失败'
    ui.showToast(msg, 'error')
  } finally {
    actionLoading.value.like = false
  }
}

async function handleFavorite() {
  if (!auth.canPost || actionLoading.value.favorite) return
  actionLoading.value.favorite = true
  try {
    const res = await toggleFavorite(post.value.id)
    const data = res?.data || {}
    const msg = res?.message || ''
    if (data.is_favorited !== undefined) {
      favorited.value = data.is_favorited
    }
    ui.showToast(msg, favorited.value ? 'success' : 'info')
  } catch (e) {
    const msg = e?.response?.data?.message || '操作失败'
    ui.showToast(msg, 'error')
  } finally {
    actionLoading.value.favorite = false
  }
}

async function submitComment() {
  if (!newComment.value.trim()) { ui.showToast('请输入评论内容', 'warning'); return }
  commentLoading.value = true
  try {
    const isReply = !!replyTo.value
    const payload = { post_id: post.value.id, content: newComment.value.trim() }
    if (replyTo.value) payload.parent_id = replyTo.value.id
    await createReply(payload)
    newComment.value = ''
    replyTo.value = null
    ui.showToast(isReply ? '回复成功' : '评论成功', 'success')
    await fetchReplies(post.value.id)
  } catch (e) {
    const msg = e?.response?.data?.message || '评论失败'
    ui.showToast(msg, 'error')
  } finally {
    commentLoading.value = false
  }
}

onMounted(() => {
  sectionStore.fetchSections()
  const id = route.params.id
  if (id) fetchPost(id)
})

watch(() => route.params.id, (newId) => {
  if (newId) fetchPost(newId)
})
</script>

<style scoped>
.post-detail { padding: var(--s-lg); }
.post-meta { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-base); }
.author-name { font-weight: 500; font-size: 14px; }
.post-time { font-size: 12px; color: var(--text-secondary); }
.post-title { font-size: 24px; font-weight: 600; margin-bottom: var(--s-base); line-height: 1.4; }
.post-content { line-height: 1.8; color: var(--text-primary); margin-bottom: var(--s-lg); }
.post-content :deep(h2) { font-size: 20px; margin: var(--s-base) 0 var(--s-sm); }
.post-content :deep(h3) { font-size: 16px; margin: var(--s-base) 0 var(--s-xs); }
.post-content :deep(code) { background: var(--bg-dark); padding: 2px 6px; border-radius: 3px; font-family: var(--mono); font-size: 13px; }
.post-content :deep(pre) { background: #1e1e1e; color: #d4d4d4; padding: var(--s-base); border-radius: var(--r-md); overflow-x: auto; margin: var(--s-base) 0; }
.post-content :deep(pre code) { background: none; padding: 0; color: inherit; }
.post-content :deep(blockquote) { border-left: 3px solid var(--primary); padding-left: var(--s-base); color: var(--text-secondary); margin: var(--s-base) 0; }
.post-actions { display: flex; gap: var(--s-sm); border-top: 1px solid var(--divider); padding-top: var(--s-base); }
.action-btn {
  display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px;
  border-radius: var(--r-sm); font-size: 13px; color: var(--text-secondary);
  transition: all var(--t-fast);
}
.action-btn:hover { background: var(--bg-dark); }
.action-btn.active { color: var(--primary); font-weight: 500; }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.comment-form { padding: var(--s-lg); border-bottom: 1px solid var(--divider); }
.guest-comment-tip { padding: var(--s-lg); border-bottom: 1px solid var(--divider); text-align: center; color: var(--text-secondary); font-size: 13px; background: var(--bg-secondary); }
.guest-tip { font-size: 12px; color: var(--warning); margin-left: auto; }
.comments-list { padding: var(--s-base) var(--s-lg); }
.comment-item { padding: var(--s-base) 0; border-bottom: 1px solid var(--divider); }
.comment-header { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-xs); }
.comment-author { font-size: 13px; font-weight: 500; }
.comment-floor { font-size: 11px; color: var(--primary); background: var(--primary-bg); padding: 1px 6px; border-radius: 999px; }
.comment-time { font-size: 12px; color: var(--text-secondary); }
.comment-body { font-size: 14px; line-height: 1.6; padding-left: 40px; }
.comment-item.nested { padding-left: 48px; background: var(--bg-secondary); border-radius: 0; }
.comment-item.nested .comment-body { padding-left: 36px; }
.comment-actions { display: flex; gap: var(--s-sm); padding-left: 40px; margin-top: var(--s-xs); }
.comment-item.nested .comment-actions { padding-left: 36px; }
.comment-action-btn {
  display: inline-flex; align-items: center; gap: 3px; font-size: 12px;
  color: var(--text-disabled); transition: color var(--t-fast);
}
.comment-action-btn:hover { color: var(--text-secondary); }
.comment-action-btn.active { color: var(--primary); }
.reply-indicator { font-size: 11px; color: var(--primary); opacity: 0.7; }
.reply-to-bar {
  display: flex; align-items: center; gap: var(--s-sm); font-size: 13px;
  color: var(--primary); margin-bottom: var(--s-sm); padding: var(--s-xs) var(--s-sm);
  background: var(--primary-bg); border-radius: var(--r-sm);
}
.cancel-reply { margin-left: auto; font-size: 12px; color: var(--text-secondary); cursor: pointer; }
.cancel-reply:hover { color: var(--error); }
.avatar-xs { width: 24px; height: 24px; border-radius: 50%; }
.empty-state { text-align: center; padding: var(--s-3xl); color: var(--text-secondary); }
</style>
