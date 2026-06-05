<template>
  <ForumHeader />
  <AppSidebar @select="() => {}" />
  <div class="forum-layout with-sidebar">
    <div class="forum-main">
      <div class="card">
        <div class="card-header">
          <div class="tabs">
            <button class="tab" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">全部收藏</button>
            <button class="tab" :class="{ active: activeTab === 'recent' }" @click="activeTab = 'recent'">最近收藏</button>
          </div>
        </div>
        <div v-for="item in filteredPosts" :key="item.id" class="fav-item">
          <div class="fav-content" @click="goToPost(item.post_id)">
            <h3 class="fav-title">{{ item.title || '（帖子已删除）' }}</h3>
            <div class="fav-meta">
              <span v-if="item.views_count">{{ item.views_count }} 浏览</span>
              <span v-if="item.views_count" class="dot">·</span>
              <span>{{ formatDate(item.created_at) }} 收藏</span>
            </div>
          </div>
          <button class="unfav-btn" @click="removeFav(item)" title="取消收藏">
            <svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
          </button>
        </div>
        <div v-if="filteredPosts.length === 0 && !loading" class="empty-state">
          <p>暂无收藏帖子</p>
        </div>
        <div v-if="loading" class="empty-state">
          <p>加载中...</p>
        </div>
        <div v-if="hasMore && !loading" class="load-more">
          <button class="btn btn-text" @click="loadMore">加载更多</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/format'
import { getMyFavorites, toggleFavorite } from '@/api/comment'

const router = useRouter()
const ui = useUIStore()
const auth = useAuthStore()
const activeTab = ref('all')
const posts = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(false)

const filteredPosts = computed(() => {
  if (activeTab.value === 'recent') {
    const weekAgo = Date.now() - 7 * 86400000
    return posts.value.filter(p => new Date(p.created_at).getTime() > weekAgo)
  }
  return posts.value
})

async function fetchFavorites(p = 1) {
  if (!auth.canPost) return
  loading.value = true
  try {
    const res = await getMyFavorites({ page, page_size: 20 })
    const data = res?.data || res || {}
    const results = data.results || []
    if (p === 1) {
      posts.value = results
    } else {
      posts.value = [...posts.value, ...results]
    }
    hasMore.value = !!data.next
    page.value = p
  } catch (e) {
    console.warn('Failed to fetch favorites:', e)
    if (p === 1) posts.value = []
  } finally {
    loading.value = false
  }
}

function loadMore() {
  fetchFavorites(page.value + 1)
}

async function removeFav(item) {
  try {
    await toggleFavorite(item.post_id)
    posts.value = posts.value.filter(p => p.id !== item.id)
    ui.showToast('已取消收藏', 'info')
  } catch (e) {
    ui.showToast('操作失败', 'error')
  }
}

function goToPost(postId) {
  router.push(`/forum/post/${postId}`)
}

onMounted(() => {
  fetchFavorites(1)
})
</script>

<style scoped>
.tabs { display: flex; gap: 0; }
.tab {
  padding: 4px 16px; font-size: 14px; font-weight: 500; color: var(--text-secondary);
  border-bottom: 2px solid transparent; transition: all var(--t-fast);
}
.tab:hover { color: var(--text-primary); }
.tab.active { color: var(--primary); border-bottom-color: var(--primary); }
.fav-item { display: flex; align-items: flex-start; padding: var(--s-lg); border-bottom: 1px solid var(--divider); gap: var(--s-base); }
.fav-content { flex: 1; cursor: pointer; }
.fav-content:hover .fav-title { color: var(--primary); }
.fav-title { font-size: 16px; font-weight: 500; margin-bottom: 4px; transition: color var(--t-fast); }
.fav-meta { font-size: 12px; color: var(--text-disabled); display: flex; gap: var(--s-xs); }
.dot { color: var(--text-disabled); }
.unfav-btn {
  flex-shrink: 0; width: 36px; height: 36px; border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center;
  color: var(--primary); transition: all var(--t-fast);
}
.unfav-btn:hover { background: rgba(244,67,54,0.08); color: var(--error); }
.empty-state { text-align: center; padding: var(--s-3xl); color: var(--text-secondary); }
.load-more { text-align: center; padding: var(--s-base); }
</style>
