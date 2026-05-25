<template>
  <ForumHeader />
  <AppSidebar @select="onSectionSelect" />
  <div class="forum-layout with-sidebar">
    <div class="forum-main">
      <div class="card">
        <PostCard v-for="post in visiblePosts" :key="post.id" :post="post" @click="goPost" />
        <div v-if="loading" class="loading-more"><span class="spinner"></span></div>
        <div v-if="!loading && visiblePosts.length === 0" class="empty-state">
          <p>暂无帖子，快来发布第一篇吧</p>
        </div>
      </div>
      <div ref="sentinel" class="scroll-sentinel"></div>
    </div>
  </div>
  <router-link v-if="!auth.isReadOnly" to="/post/new" class="fab" title="发帖">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  </router-link>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import ForumHeader from '@/components/ForumHeader.vue'
import AppSidebar from '@/components/AppSidebar.vue'
import PostCard from '@/components/PostCard.vue'
import { useSectionStore } from '@/stores/section'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const sectionStore = useSectionStore()
const auth = useAuthStore()
const PAGE_SIZE = 10
const loading = ref(false)
const displayCount = ref(PAGE_SIZE)
const sentinel = ref(null)
let observer = null

const allPosts = ref([])

const filteredPosts = computed(() => {
  if (sectionStore.activeSection === 'all') return allPosts.value
  return allPosts.value.filter(p => p.section === sectionStore.activeSection)
})

const visiblePosts = computed(() => filteredPosts.value.slice(0, displayCount.value))
const hasMore = computed(() => displayCount.value < filteredPosts.value.length)

function onSectionSelect() { displayCount.value = PAGE_SIZE }

function loadMore() {
  if (loading.value || !hasMore.value) return
  loading.value = true
  setTimeout(() => {
    displayCount.value += PAGE_SIZE
    loading.value = false
  }, 400)
}

function goPost(post) { router.push(`/post/${post.id}`) }

onMounted(() => {
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
