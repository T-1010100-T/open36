<template>
  <ForumHeader />
  <AppSidebar @select="() => {}" />
  <div class="forum-layout with-sidebar">
    <div class="forum-main">
      <div class="card profile-header">
        <img :src="user.avatar" class="avatar avatar-xl" />
        <div class="profile-info">
          <h1 class="profile-name">{{ user.nickname }}</h1>
          <div class="profile-username">@{{ user.username }}</div>
          <p class="profile-bio">{{ user.bio }}</p>
          <div class="profile-stats">
            <div class="stat-item"><span class="stat-value">{{ formatNumber(user.stats.posts) }}</span><span class="stat-label">帖子</span></div>
            <div class="stat-item"><span class="stat-value">{{ formatNumber(user.stats.replies) }}</span><span class="stat-label">回复</span></div>
            <div class="stat-item"><span class="stat-value">{{ formatNumber(user.stats.likes) }}</span><span class="stat-label">获赞</span></div>
            <div class="stat-item"><span class="stat-value">{{ formatNumber(user.stats.favorites) }}</span><span class="stat-label">收藏</span></div>
          </div>
          <div v-if="algoStats.loaded && (algoStats.acCount > 0 || algoStats.submitCount > 0)" class="profile-stats algo-stats">
            <div class="stat-item"><span class="stat-value">{{ formatNumber(algoStats.acCount) }}</span><span class="stat-label">通过题数</span></div>
            <div class="stat-item"><span class="stat-value">{{ formatNumber(algoStats.submitCount) }}</span><span class="stat-label">提交次数</span></div>
            <div class="stat-item"><span class="stat-value">{{ formatNumber(algoStats.rating) }}</span><span class="stat-label">Rating</span></div>
            <div class="stat-item"><span class="stat-value">{{ formatNumber(algoStats.streak) }}</span><span class="stat-label">连续打卡</span></div>
          </div>
          <div class="profile-joined">加入于 {{ user.joinDate }}</div>
        </div>
      </div>
      <div class="card" style="margin-top: var(--s-base)">
        <div class="tabs">
          <button class="tab" :class="{ active: activeTab === 'posts' }" @click="activeTab = 'posts'">发帖历史</button>
          <button class="tab" :class="{ active: activeTab === 'replies' }" @click="activeTab = 'replies'">回复历史</button>
        </div>
        <div v-if="activeTab === 'posts'">
          <div v-for="p in posts" :key="p.id" class="history-item">
            <h3 class="history-title">{{ p.title }}</h3>
            <div class="history-meta">{{ formatDate(p.createdAt) }} · {{ p.votes }} 赞 · {{ p.replyCount }} 回复</div>
          </div>
        </div>
        <div v-else>
          <div v-for="r in replies" :key="r.id" class="history-item">
            <div class="history-meta">回复了《{{ r.postTitle }}》</div>
            <p class="history-content">{{ r.content }}</p>
            <div class="history-meta">{{ formatDate(r.createdAt) }} · {{ r.votes }} 赞</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { formatDate, formatNumber } from '@/utils/format'
import { getHojUserStats } from '@/api/hoj'

const route = useRoute()
const auth = useAuthStore()
const activeTab = ref('posts')

const isCurrentUser = computed(() => {
  return !route.params.id || route.params.id === String(auth.user?.id)
})

const user = computed(() => {
  if (isCurrentUser.value && auth.user) {
    const name = auth.user.nickname || auth.user.username
    return {
      id: auth.user.id,
      nickname: name,
      username: auth.user.username,
      avatar: auth.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=1976D2&color=fff&size=120`,
      bio: '暂无简介',
      joinDate: '2025-03-15',
      stats: { posts: 0, replies: 0, likes: 0, favorites: 0 }
    }
  }
  return {
    id: route.params.id || '1', nickname: '未知用户', username: '',
    avatar: `https://ui-avatars.com/api/?name=U&background=1976D2&color=fff&size=120`,
    bio: '',
    joinDate: '',
    stats: { posts: 0, replies: 0, likes: 0, favorites: 0 }
  }
})

const algoStats = ref({ acCount: 0, submitCount: 0, rating: 0, streak: 0, loaded: false })

async function fetchAlgoStats() {
  const username = user.value.username
  if (!username) return
  const stats = await getHojUserStats(username)
  if (stats) {
    algoStats.value = { ...stats, loaded: true }
  } else {
    algoStats.value = { acCount: 0, submitCount: 0, rating: 0, streak: 0, loaded: true }
  }
}

onMounted(() => {
  fetchAlgoStats()
})

watch(() => route.params.id, () => {
  fetchAlgoStats()
})

const posts = ref([])

const replies = ref([])
</script>

<style scoped>
.profile-header { display: flex; gap: var(--s-xl); padding: var(--s-xl); align-items: flex-start; }
.profile-info { flex: 1; }
.profile-name { font-size: 24px; font-weight: 600; margin-bottom: 2px; }
.profile-username { font-size: 14px; color: var(--text-secondary); margin-bottom: var(--s-sm); }
.profile-bio { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: var(--s-base); }
.profile-stats { display: flex; gap: var(--s-xl); margin-bottom: var(--s-sm); }
.stat-item { display: flex; flex-direction: column; align-items: center; }
.stat-value { font-size: 20px; font-weight: 600; color: var(--text-primary); }
.stat-label { font-size: 12px; color: var(--text-secondary); }
.profile-joined { font-size: 12px; color: var(--text-disabled); }
.algo-stats { margin-top: var(--s-sm); flex-wrap: wrap; }
.algo-stats .stat-value { color: var(--primary); }
.tabs { display: flex; border-bottom: 1px solid var(--divider); }
.tab {
  padding: var(--s-base) var(--s-lg); font-size: 14px; font-weight: 500;
  color: var(--text-secondary); border-bottom: 2px solid transparent; transition: all var(--t-fast);
}
.tab:hover { color: var(--text-primary); }
.tab.active { color: var(--primary); border-bottom-color: var(--primary); }
.history-item { padding: var(--s-base) var(--s-lg); border-bottom: 1px solid var(--divider); }
.history-title { font-size: 15px; font-weight: 500; margin-bottom: 4px; }
.history-content { font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 4px; }
.history-meta { font-size: 12px; color: var(--text-disabled); }
@media (max-width: 599px) {
  .profile-header { flex-direction: column; align-items: center; text-align: center; }
  .profile-stats { justify-content: center; }
}
</style>
