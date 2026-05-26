<template>
  <ForumHeader />
  <AppSidebar @select="onSectionSelect" />
  <div class="forum-layout with-sidebar">
    <div class="forum-main">
      <div class="card">
        <PostCard v-for="post in visiblePosts" :key="post.id" :post="post" @click="goPost" />
        <div v-if="loading" class="loading-more"><span class="spinner"></span></div>
        <div v-if="!loading && visiblePosts.length === 0" class="empty-state">
          <p>{{ fetchError || '暂无帖子，快来发布第一篇吧' }}</p>
        </div>
      </div>
      <div ref="sentinel" class="scroll-sentinel"></div>
    </div>
  </div>
  <router-link v-if="auth.canPost" to="/post/new" class="fab" title="发帖">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  </router-link>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import PostCard from '@/components/PostCard.vue'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { getPosts } from '@/api/post'

const router = useRouter()
const sectionStore = useSectionStore()
const auth = useAuthStore()
const ui = useUIStore()
const fetchError = ref('')
const PAGE_SIZE = 10
const loading = ref(false)
const allPosts = ref([])
const currentPage = ref(1)
const totalCount = ref(0)
const sentinel = ref(null)
let observer = null

const activeSectionId = computed(() => {
  const key = sectionStore.activeSection
  if (key === 'all') return null
  return sectionStore.getSectionId(key)
})

const visiblePosts = computed(() => allPosts.value)
const hasMore = computed(() => allPosts.value.length < totalCount.value)

async function fetchPosts(page = 1) {
  loading.value = true
  try {
    const params = { page, page_size: PAGE_SIZE }
    if (activeSectionId.value) params.section_id = activeSectionId.value
    const res = await getPosts(params)
    const data = res?.data || {}
    totalCount.value = data.count || 0
    const results = data.results || []
    // 转换字段以适配 PostCard
    const mapped = results.map(p => {
      const sec = sectionStore.getSectionById(p.section?.section_id)
      return {
        id: p.id,
        title: p.title,
        content: p.content_preview || p.content || '',
        author: p.author?.nickname || `用户${p.author?.user_id || ''}`,
        section: sec?.key || '',
        votes: p.likes_count || 0,
        replyCount: p.replies_count || 0,
        shareCount: 0,
        pinned: p.is_pinned,
        createdAt: p.created_at
      }
    })
    if (page === 1) {
      allPosts.value = mapped
    } else {
      allPosts.value.push(...mapped)
    }
    currentPage.value = page
  } catch (e) {
    const msg = e?.response?.data?.message || e?.message || '加载失败'
    fetchError.value = msg
    console.warn('Failed to fetch posts:', e)
  } finally {
    loading.value = false
  }
}

function onSectionSelect() {
  currentPage.value = 1
  fetchPosts(1)
}

function loadMore() {
  if (loading.value || !hasMore.value) return
  fetchPosts(currentPage.value + 1)
}

function goPost(post) { router.push(`/post/${post.id}`) }

onMounted(() => {
  sectionStore.fetchSections()
  fetchPosts(1)
  observer = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) loadMore() }, { rootMargin: '200px' })
  if (sentinel.value) observer.observe(sentinel.value)
})
onUnmounted(() => { observer?.disconnect() })
</script>

<style scoped>
.scroll-sentinel { height: 1px; }
.loading-more { display: flex; justify-content: center; padding: var(--s-lg); }
.empty-state { text-align: center; padding: var(--s-3xl); color: var(--text-secondary); }
.fab {
  position: fixed; bottom: var(--s-xl); right: var(--s-xl);
  width: 56px; height: 56px; border-radius: 50%; background: var(--primary);
  color: #fff; display: flex; align-items: center; justify-content: center;
  box-shadow: var(--sh-lg); transition: all var(--t-fast); z-index: 40;
}
.fab:hover { transform: scale(1.1); background: var(--primary-dark); }
@media (max-width: 959px) { .fab { bottom: var(--s-lg); right: var(--s-lg); } }
</style>
