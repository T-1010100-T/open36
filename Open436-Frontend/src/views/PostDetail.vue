<template>
  <ForumHeader />
  <AppSidebar @select="() => {}" />
  <div class="forum-layout with-sidebar">
    <div class="forum-main">
      <div class="card">
        <div class="post-detail">
          <div class="post-meta">
            <img :src="`https://ui-avatars.com/api/?name=${post.author}&background=1976D2&color=fff&size=40`" class="avatar" />
            <div>
              <div class="author-name">u/{{ post.author }}</div>
              <div class="post-time">{{ formatDate(post.createdAt) }} · {{ sectionName }}</div>
            </div>
          </div>
          <h1 class="post-title">{{ post.title }}</h1>
          <div class="post-content" v-html="postHtml"></div>
          <div class="post-actions">
            <button v-if="!auth.isReadOnly" class="action-btn" :class="{ active: liked }" @click="liked = !liked">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>
              {{ liked ? post.votes + 1 : post.votes }}
            </button>
            <button v-if="!auth.isReadOnly" class="action-btn" :class="{ active: favorited }" @click="favorited = !favorited">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
              {{ favorited ? '已收藏' : '收藏' }}
            </button>
            <button class="action-btn" @click="shareRef.open()">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
              分享
            </button>
            <router-link v-if="!auth.isReadOnly" to="/post/new" class="action-btn">编辑</router-link>
            <button v-if="!auth.isReadOnly" class="action-btn danger" @click="confirmRef.show('确定删除此帖子？', () => {})">删除</button>
            <span v-if="auth.isReadOnly" class="guest-tip">游客模式仅可浏览</span>
          </div>
        </div>
      </div>
      <div class="card" style="margin-top: var(--s-base)">
        <div class="card-header">评论 ({{ totalComments }})</div>
        <div v-if="!auth.isReadOnly" class="comment-form">
          <textarea v-model="newComment" class="form-textarea" placeholder="写下你的评论..." rows="3"></textarea>
          <button class="btn btn-primary btn-sm" style="margin-top: var(--s-sm)" @click="submitComment">发表评论</button>
        </div>
        <div v-else class="guest-comment-tip">
          <span>游客模式仅可浏览，报名审核通过后可发表评论</span>
        </div>
        <div class="comments-list">
          <template v-for="c in comments" :key="c.id">
            <CommentNode :comment="c" :depth="0" />
          </template>
        </div>
      </div>
    </div>
  </div>
  <ShareModal ref="shareRef" />
  <ConfirmDialog ref="confirmRef" />
</template>

<script setup>
import { ref, computed, h, defineComponent } from 'vue'
import { useRoute } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import ShareModal from '@/components/ShareModal.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useSectionStore } from '@/stores/section'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { formatDate, markdownToHtml } from '@/utils/format'

const route = useRoute()
const sectionStore = useSectionStore()
const ui = useUIStore()
const auth = useAuthStore()
const shareRef = ref(null)
const confirmRef = ref(null)
const liked = ref(false)
const favorited = ref(false)
const newComment = ref('')

const CommentNode = defineComponent({
  name: 'CommentNode',
  props: { comment: Object, depth: { type: Number, default: 0 } },
  setup(props) {
    return () => {
      const c = props.comment
      const indent = Math.min(props.depth, 4) * 24
      return h('div', { class: 'comment-item', style: { marginLeft: indent + 'px' } }, [
        h('div', { class: 'comment-header' }, [
          h('img', { src: `https://ui-avatars.com/api/?name=${c.author}&background=1976D2&color=fff&size=32`, class: 'avatar avatar-sm' }),
          h('span', { class: 'comment-author' }, 'u/' + c.author),
          h('span', { class: 'comment-time' }, formatDate(c.createdAt))
        ]),
        h('div', { class: 'comment-body' }, c.content),
        h('div', { class: 'comment-actions' }, auth.isReadOnly ? [] : [
          h('button', { class: 'action-btn btn-sm' }, '回复')
        ]),
        ...(c.children || []).map(child => h(CommentNode, { comment: child, depth: props.depth + 1, key: child.id }))
      ])
    }
  }
})

const post = ref(null)

const sectionName = computed(() => sectionStore.getSection(post.value.section)?.name || '')
const postHtml = computed(() => markdownToHtml(post.value.content))

const comments = ref([])

const totalComments = computed(() => {
  function count(arr) { return arr.reduce((n, c) => n + 1 + count(c.children || []), 0) }
  return count(comments.value)
})

function submitComment() {
  if (!newComment.value.trim()) { ui.showToast('请输入评论内容', 'warning'); return }
  comments.value.push({ id: Date.now(), author: '我', content: newComment.value, createdAt: new Date().toISOString(), children: [] })
  newComment.value = ''
  ui.showToast('评论成功', 'success')
}
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
.action-btn.danger:hover { color: var(--error); }
.comment-form { padding: var(--s-lg); border-bottom: 1px solid var(--divider); }
.guest-comment-tip { padding: var(--s-lg); border-bottom: 1px solid var(--divider); text-align: center; color: var(--text-secondary); font-size: 13px; background: var(--bg-secondary); }
.guest-tip { font-size: 12px; color: var(--warning); margin-left: auto; }
.comments-list { padding: var(--s-base) var(--s-lg); }
.comment-item { padding: var(--s-base) 0; border-bottom: 1px solid var(--divider); }
.comment-header { display: flex; align-items: center; gap: var(--s-sm); margin-bottom: var(--s-xs); }
.comment-author { font-size: 13px; font-weight: 500; }
.comment-time { font-size: 12px; color: var(--text-secondary); }
.comment-body { font-size: 14px; line-height: 1.6; padding-left: 40px; }
.comment-actions { padding-left: 40px; margin-top: var(--s-xs); }
</style>
