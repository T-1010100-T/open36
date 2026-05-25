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
        <div v-for="post in filteredPosts" :key="post.id" class="fav-item">
          <div class="fav-content">
            <h3 class="fav-title">{{ post.title }}</h3>
            <p class="fav-preview">{{ post.content }}</p>
            <div class="fav-meta">
              <span>u/{{ post.author }}</span>
              <span class="dot">·</span>
              <span>{{ formatDate(post.createdAt) }}</span>
              <span class="dot">·</span>
              <span>{{ post.votes }} 赞</span>
            </div>
          </div>
          <button class="unfav-btn" @click="removeFav(post.id)" title="取消收藏">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
          </button>
        </div>
        <div v-if="filteredPosts.length === 0" class="empty-state">
          <p>暂无收藏帖子</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ForumHeader from '@/components/ForumHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import { useUIStore } from '@/stores/ui'
import { formatDate } from '@/utils/format'

const ui = useUIStore()
const activeTab = ref('all')

const posts = ref([])

const filteredPosts = computed(() => {
  if (activeTab.value === 'recent') {
    const weekAgo = Date.now() - 7 * 86400000
    return posts.value.filter(p => new Date(p.favoritedAt).getTime() > weekAgo)
  }
  return posts.value
})

function removeFav(id) {
  posts.value = posts.value.filter(p => p.id !== id)
  ui.showToast('已取消收藏', 'info')
}
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
.fav-title { font-size: 16px; font-weight: 500; margin-bottom: 4px; }
.fav-preview { font-size: 13px; color: var(--text-secondary); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: var(--s-xs); }
.fav-meta { font-size: 12px; color: var(--text-disabled); display: flex; gap: var(--s-xs); }
.dot { color: var(--text-disabled); }
.unfav-btn {
  flex-shrink: 0; width: 36px; height: 36px; border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center;
  color: var(--primary); transition: all var(--t-fast);
}
.unfav-btn:hover { background: rgba(244,67,54,0.08); color: var(--error); }
.empty-state { text-align: center; padding: var(--s-3xl); color: var(--text-secondary); }
</style>
