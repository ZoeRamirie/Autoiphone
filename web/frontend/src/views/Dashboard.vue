<script setup>
import { ref } from 'vue'

const stats = ref([
  { name: '今日外呼', value: '1,240', change: '+12%', up: true, icon: 'M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z' },
  { name: '接通率', value: '45.2%', change: '+5.4%', up: true, icon: 'M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z' },
  { name: '高意向客户', value: '89', change: '-2', up: false, icon: 'M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z' },
  { name: '均通话时长', value: '1m24s', change: '+12s', up: true, icon: 'M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z' }
])

const activities = ref([
  { phone: '138****1234', text: '接通 3m10s · 高意向 · 已提取微信', time: '10 分钟前', level: 'high' },
  { phone: '159****9876', text: '客户直接拒接', time: '15 分钟前', level: 'reject' },
  { phone: '188****5555', text: '接通 15s · 无明确意向', time: '30 分钟前', level: 'low' },
  { phone: '136****4321', text: '接通 2m45s · 中意向 · 要求发资料', time: '45 分钟前', level: 'mid' },
  { phone: '177****8888', text: '无人接听', time: '1 小时前', level: 'none' }
])

const levelColors = {
  high: '#22C55E',
  mid: '#EAB308',
  low: '#94A3B8',
  reject: '#EF4444',
  none: '#64748B'
}
</script>

<template>
  <div class="space-y-6">
    <!-- 顶部标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold" style="color: var(--text-primary);">总览大盘</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">实时监控 AI 外呼系统运行状态</p>
      </div>
      <button class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-white cursor-pointer transition-all duration-200 hover:opacity-90"
        style="background: var(--primary);">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
        </svg>
        启动群呼任务
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="item in stats" :key="item.name"
        class="rounded-xl p-5 border transition-all duration-200 cursor-pointer"
        style="background: var(--bg-card); border-color: var(--border);"
        onmouseover="this.style.borderColor='var(--primary)'"
        onmouseout="this.style.borderColor='var(--border)'"
      >
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium" style="color: var(--text-muted);">{{ item.name }}</span>
          <div class="w-9 h-9 rounded-lg flex items-center justify-center" style="background: var(--bg-elevated);">
            <svg class="w-4.5 h-4.5" style="color: var(--primary-light);" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
            </svg>
          </div>
        </div>
        <div class="flex items-end gap-2">
          <span class="text-3xl font-bold font-mono" style="color: var(--text-primary);">{{ item.value }}</span>
          <span class="text-xs font-medium mb-1 px-1.5 py-0.5 rounded"
            :style="{ background: item.up ? '#22C55E20' : '#EF444420', color: item.up ? '#22C55E' : '#EF4444' }">
            {{ item.change }}
          </span>
        </div>
      </div>
    </div>

    <!-- 实时动态 -->
    <div class="rounded-xl border overflow-hidden" style="background: var(--bg-card); border-color: var(--border);">
      <div class="px-5 py-4 border-b flex items-center justify-between" style="border-color: var(--border);">
        <h3 class="text-sm font-semibold" style="color: var(--text-primary);">实时外呼动态</h3>
        <div class="flex items-center gap-1.5">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" style="background: var(--success);"></span>
            <span class="relative inline-flex rounded-full h-2 w-2" style="background: var(--success);"></span>
          </span>
          <span class="text-xs" style="color: var(--text-muted);">实时更新中</span>
        </div>
      </div>
      <div class="divide-y" style="border-color: var(--border);">
        <div v-for="(a, i) in activities" :key="i"
          class="flex items-center justify-between px-5 py-3.5 transition-colors duration-150 cursor-pointer"
          onmouseover="this.style.background='var(--bg-elevated)'"
          onmouseout="this.style.background='transparent'"
        >
          <div class="flex items-center gap-3">
            <div class="w-2 h-2 rounded-full shrink-0" :style="{ background: levelColors[a.level] }"></div>
            <div>
              <span class="text-sm font-mono font-medium" style="color: var(--text-primary);">{{ a.phone }}</span>
              <p class="text-xs mt-0.5" style="color: var(--text-muted);">{{ a.text }}</p>
            </div>
          </div>
          <span class="text-xs shrink-0 ml-4" style="color: var(--text-muted);">{{ a.time }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
