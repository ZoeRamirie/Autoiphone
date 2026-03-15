<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const navigation = [
  { name: '总览大盘', path: '/', icon: 'M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6' },
  { name: '客户管理', path: '/customers', icon: 'M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z' },
  { name: 'AI 外呼', path: '#', icon: 'M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z' },
  { name: '声音克隆', path: '#', icon: 'M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z' }
]
</script>

<template>
  <div class="min-h-screen flex" style="background: var(--bg-base); color: var(--text-primary);">
    <!-- 侧边栏 -->
    <aside class="w-64 flex flex-col border-r" style="background: var(--bg-card); border-color: var(--border);">
      <!-- Logo -->
      <div class="h-16 flex items-center px-5 border-b" style="border-color: var(--border);">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center mr-3" style="background: var(--primary);">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z" />
          </svg>
        </div>
        <span class="font-semibold text-lg tracking-tight" style="color: var(--text-primary);">Autoiphone</span>
      </div>

      <!-- 导航 -->
      <nav class="flex-1 py-4 px-3 space-y-1">
        <router-link
          v-for="item in navigation"
          :key="item.path"
          :to="item.path"
          class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg cursor-pointer transition-all duration-200"
          :style="{
            background: route.path === item.path ? 'var(--primary)' : 'transparent',
            color: route.path === item.path ? '#fff' : 'var(--text-secondary)'
          }"
        >
          <svg class="w-5 h-5 mr-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
          </svg>
          {{ item.name }}
        </router-link>
      </nav>

      <!-- 底部状态 -->
      <div class="p-4 border-t" style="border-color: var(--border);">
        <div class="flex items-center gap-3 px-1">
          <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold" style="background: var(--bg-elevated); color: var(--primary-light);">A</div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate" style="color: var(--text-primary);">管理员</p>
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full" style="background: var(--success);"></span>
              <span class="text-xs" style="color: var(--text-muted);">系统在线</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- 主区域 -->
    <main class="flex-1 flex flex-col h-screen overflow-hidden">
      <!-- 顶栏 -->
      <header class="h-14 flex items-center justify-between px-6 border-b" style="background: var(--bg-card); border-color: var(--border);">
        <span class="text-sm" style="color: var(--text-muted);">
          工作台 / <span style="color: var(--text-primary);">{{ navigation.find(n => n.path === route.path)?.name || '页面' }}</span>
        </span>
      </header>

      <!-- 内容区 -->
      <div class="flex-1 overflow-auto p-6" style="background: var(--bg-base);">
        <router-view />
      </div>
    </main>
  </div>
</template>
