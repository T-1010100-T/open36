<template>
  <div class="algo-loading">
    <p>正在进入算法系统...</p>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

onMounted(async () => {
  if (auth.isLoggedIn && !auth.isVisitor) {
    await auth.syncToHoj()
  }
  window.location.href = '/algo/'
})
</script>

<style scoped>
.algo-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  color: #909399;
  font-size: 14px;
}
</style>
