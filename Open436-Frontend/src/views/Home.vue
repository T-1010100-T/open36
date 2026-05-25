<template>
  <div class="landing">
    <!-- Navbar override for landing -->
    <nav class="landing-nav">
      <router-link to="/" class="landing-brand">
        <div class="brand-mark">O</div>
        <span>OPEN436</span>
      </router-link>
      <div class="landing-nav-links">
        <router-link to="/forum">论坛</router-link>
        <a href="javascript:void(0)" @click="goToAlgo">算法</a>
      </div>
      <div class="landing-nav-right">
        <router-link v-if="!auth.isLoggedIn" to="/login" class="nav-login">登录</router-link>
        <div v-else class="nav-mine-wrap">
          <router-link to="/mine" class="nav-login">我的</router-link>
          <button class="nav-mine-arrow" @click="mineOpen = !mineOpen">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
          </button>
          <div class="nav-mine-dropdown" :class="{ active: mineOpen }">
            <router-link to="/mine" class="nm-item" @click="mineOpen = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="15" height="15"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              个人中心
            </router-link>
            <router-link to="/profile/edit" class="nm-item" @click="mineOpen = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="15" height="15"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              编辑资料
            </router-link>
            <div class="nm-label">更多</div>
            <router-link to="/favorites" class="nm-item" @click="mineOpen = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="15" height="15"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>
              我的收藏
            </router-link>
            <router-link to="/password/change" class="nm-item" @click="mineOpen = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="15" height="15"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              修改密码
            </router-link>
          </div>
        </div>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero">
      <div class="hero-grid"></div>
      <div class="hero-glow"></div>
      <div class="hero-content">
        <div class="hero-label">0436 技术社区</div>
        <h1 class="hero-title">
          <span class="line">OPEN436</span>
          <span class="line sub">为技术而生</span>
        </h1>
        <p class="hero-desc">
          一个开放协作的技术平台。交流、刷题、成长，与志同道合的人一起探索技术的边界。
        </p>
      </div>

      <!-- Scroll hint -->
      <div class="scroll-hint">
        <div class="scroll-line"></div>
      </div>
    </section>

    <!-- Stats -->
    <section class="stats">
      <div class="stats-inner">
        <div class="stat-item">
          <div class="stat-num">0</div>
          <div class="stat-label">社区成员</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-num">0</div>
          <div class="stat-label">技术帖子</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-num">0</div>
          <div class="stat-label">算法题解</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-num">∞</div>
          <div class="stat-label">成长可能</div>
        </div>
      </div>
    </section>

    <!-- Manifesto -->
    <section class="manifesto">
      <div class="manifesto-inner">
        <div class="manifesto-text">
          <h2>开放源代码<br/>开放思想<br/>开放未来</h2>
        </div>
        <div class="manifesto-desc">
          <p>我们相信技术的力量源于分享与协作。Open436 不仅是一个平台，更是一种态度——对知识的敬畏，对未知的好奇，对卓越的追求。</p>
          <p>无论你是刚入门的新手，还是经验丰富的开发者，这里都有你的一席之地。</p>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="footer-inner">
        <div class="footer-left">
          <div class="footer-brand">
            <div class="brand-mark">O</div>
            <span>OPEN436</span>
          </div>
          <p class="footer-slogan">0436 技术社区</p>
        </div>
        <div class="footer-links">
          <router-link to="/forum">论坛</router-link>
          <a href="javascript:void(0)" @click="goToAlgo">算法</a>
          <router-link to="/login">登录</router-link>
        </div>
      </div>
      <div class="footer-copy"> Open436. All rights reserved.</div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'

const auth = useAuthStore()
const ui = useUIStore()
const mineOpen = ref(false)

document.addEventListener('click', (e) => {
  if (!e.target.closest('.nav-mine-wrap')) mineOpen.value = false
})

async function goToAlgo() {
  if (auth.isGuest) {
    ui.showToast('审核通过后方可进入算法平台', 'warning')
    return
  }
  if (auth.isLoggedIn && !auth.isVisitor) {
    await auth.syncToHoj()
  }
  window.location.href = '/algo/'
}
</script>

<style scoped>
.landing {
  --landing-bg: #0a0e1a;
  --landing-surface: rgba(255,255,255,0.03);
  --landing-border: rgba(255,255,255,0.06);
  --landing-text: #e8ecf1;
  --landing-muted: #6b7a94;
  --landing-accent: #4f8cff;
  --landing-accent-dim: rgba(79,140,255,0.12);
}

/* Nav */
.landing-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: 64px; display: flex; align-items: center;
  padding: 0 48px;
  background: rgba(10,14,26,0.7);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--landing-border);
}
.landing-brand {
  display: flex; align-items: center; gap: 10px;
  color: var(--landing-text); text-decoration: none; font-weight: 700; font-size: 16px; letter-spacing: 1px;
}
.brand-mark {
  width: 30px; height: 30px; border-radius: 7px;
  background: linear-gradient(135deg, var(--landing-accent), #2d5fcc);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 14px; font-weight: 800;
}
.landing-nav-links {
  display: flex; gap: 32px; margin-left: 64px;
}
.landing-nav-links a {
  color: var(--landing-muted); text-decoration: none; font-size: 14px;
  transition: color 0.2s;
}
.landing-nav-links a:hover { color: var(--landing-text); }
.landing-nav-right { margin-left: auto; }
.nav-login {
  color: var(--landing-text); text-decoration: none; font-size: 14px; font-weight: 500;
  padding: 6px 18px; border-radius: 6px;
  border: 1px solid var(--landing-border);
  transition: all 0.2s;
}
.nav-login:hover { border-color: var(--landing-accent); color: var(--landing-accent); }

.nav-mine-wrap { position: relative; display: flex; align-items: center; }
.nav-mine-arrow {
  margin-left: -1px; padding: 6px 8px 6px 2px; border-left: none;
  border: 1px solid var(--landing-border); border-left: none;
  border-radius: 0 6px 6px 0; color: var(--landing-muted);
  background: none; cursor: pointer; transition: all 0.2s; display: flex; align-items: center;
}
.nav-mine-wrap:hover .nav-mine-arrow { border-color: var(--landing-accent); color: var(--landing-accent); }
.nav-mine-dropdown {
  position: absolute; top: 100%; right: 0; margin-top: 8px;
  background: #1a1f2e; border: 1px solid var(--landing-border); border-radius: 8px;
  min-width: 180px; padding: 6px; opacity: 0; visibility: hidden;
  transform: translateY(-8px); transition: all 0.2s; z-index: 101;
}
.nav-mine-dropdown.active { opacity: 1; visibility: visible; transform: translateY(0); }
.nm-item {
  display: flex; align-items: center; gap: 8px; padding: 9px 12px;
  color: var(--landing-muted); font-size: 13px; border-radius: 5px;
  text-decoration: none; transition: all 0.15s;
}
.nm-item:hover { background: rgba(255,255,255,0.06); color: var(--landing-text); }
.nm-label {
  padding: 8px 12px 4px; font-size: 10px; font-weight: 600;
  color: rgba(255,255,255,0.25); text-transform: uppercase; letter-spacing: 0.5px;
}

@media (max-width: 768px) {
  .landing-nav { padding: 0 20px; }
  .landing-nav-links { display: none; }
}

/* Hero */
.hero {
  position: relative; min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  background: var(--landing-bg);
  overflow: hidden;
  padding: 120px 24px 80px;
}
.hero-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(79,140,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(79,140,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 70%);
}
.hero-glow {
  position: absolute; width: 600px; height: 600px; border-radius: 50%;
  background: radial-gradient(circle, rgba(79,140,255,0.08), transparent 60%);
  top: 50%; left: 50%; transform: translate(-50%, -55%);
  pointer-events: none;
}
.hero-content {
  position: relative; z-index: 1; text-align: center; max-width: 720px;
  animation: fadeUp 1s cubic-bezier(0.4,0,0.2,1) both;
}
.hero-label {
  display: inline-block; font-size: 12px; font-weight: 500;
  color: var(--landing-accent); letter-spacing: 3px; text-transform: uppercase;
  margin-bottom: 24px; padding: 6px 16px;
  background: var(--landing-accent-dim); border-radius: 999px;
}
.hero-title {
  font-size: clamp(48px, 10vw, 96px); font-weight: 800;
  color: var(--landing-text); line-height: 1.05; letter-spacing: -3px;
  margin-bottom: 24px;
}
.hero-title .line { display: block; }
.hero-title .sub {
  font-size: 0.45em; font-weight: 400; letter-spacing: 8px;
  color: var(--landing-muted); margin-top: 12px;
}
.hero-desc {
  font-size: 17px; color: var(--landing-muted); line-height: 1.7;
  max-width: 480px; margin: 0 auto 40px;
}

/* CTA */
.hero-cta {
  display: flex; gap: 16px; justify-content: center; flex-wrap: wrap;
}
.cta-primary {
  display: inline-flex; align-items: center; gap: 8px;
  height: 44px; padding: 0 28px; border-radius: 8px;
  background: var(--landing-accent); color: #fff;
  font-size: 14px; font-weight: 600; text-decoration: none;
  transition: all 0.2s;
}
.cta-primary:hover { background: #3a7aee; transform: translateY(-1px); }
.cta-secondary {
  display: inline-flex; align-items: center;
  height: 44px; padding: 0 28px; border-radius: 8px;
  border: 1px solid var(--landing-border); color: var(--landing-text);
  font-size: 14px; font-weight: 500; text-decoration: none;
  transition: all 0.2s;
}
.cta-secondary:hover { border-color: var(--landing-muted); }

/* Scroll hint */
.scroll-hint {
  position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%);
}
.scroll-line {
  width: 1px; height: 40px; background: var(--landing-border); position: relative; overflow: hidden;
}
.scroll-line::after {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 50%;
  background: var(--landing-accent);
  animation: scrollPulse 2s ease-in-out infinite;
}
@keyframes scrollPulse {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(200%); }
}

/* Stats */
.stats {
  background: var(--landing-bg);
  border-top: 1px solid var(--landing-border);
  border-bottom: 1px solid var(--landing-border);
  padding: 64px 24px;
}
.stats-inner {
  max-width: 900px; margin: 0 auto;
  display: flex; align-items: center; justify-content: center; gap: 48px;
}
.stat-item { text-align: center; }
.stat-num {
  font-size: 36px; font-weight: 700; color: var(--landing-text);
  font-variant-numeric: tabular-nums; letter-spacing: -1px;
}
.stat-label {
  font-size: 13px; color: var(--landing-muted); margin-top: 6px; letter-spacing: 1px;
}
.stat-divider {
  width: 1px; height: 40px; background: var(--landing-border);
}
@media (max-width: 768px) {
  .stats-inner { flex-wrap: wrap; gap: 32px; }
  .stat-divider { display: none; }
  .stat-item { min-width: 100px; }
}

/* Manifesto */
.manifesto {
  background: var(--landing-bg); padding: 120px 24px;
}
.manifesto-inner {
  max-width: 1000px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center;
}
.manifesto-text h2 {
  font-size: clamp(32px, 5vw, 48px); font-weight: 800;
  color: var(--landing-text); line-height: 1.2; letter-spacing: -1px;
}
.manifesto-desc p {
  font-size: 16px; color: var(--landing-muted); line-height: 1.8;
  margin-bottom: 20px;
}
.manifesto-desc p:last-child { margin-bottom: 0; }
@media (max-width: 768px) {
  .manifesto-inner { grid-template-columns: 1fr; gap: 40px; }
  .manifesto-text h2 { font-size: 32px; }
}

/* Footer */
.landing-footer {
  background: #070a14; padding: 48px;
  border-top: 1px solid var(--landing-border);
}
.footer-inner {
  max-width: 1000px; margin: 0 auto;
  display: flex; align-items: center; justify-content: space-between;
}
.footer-brand {
  display: flex; align-items: center; gap: 10px;
  color: var(--landing-text); font-weight: 700; font-size: 15px; letter-spacing: 1px;
}
.footer-slogan {
  font-size: 12px; color: var(--landing-muted); margin-top: 4px; margin-left: 40px;
}
.footer-links {
  display: flex; gap: 32px;
}
.footer-links a {
  color: var(--landing-muted); text-decoration: none; font-size: 13px;
  transition: color 0.2s;
}
.footer-links a:hover { color: var(--landing-text); }
.footer-copy {
  text-align: center; font-size: 12px; color: var(--landing-muted);
  margin-top: 32px; padding-top: 24px;
  border-top: 1px solid var(--landing-border);
}
@media (max-width: 768px) {
  .landing-footer { padding: 32px 24px; }
  .footer-inner { flex-direction: column; gap: 24px; align-items: flex-start; }
  .footer-slogan { margin-left: 0; }
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
