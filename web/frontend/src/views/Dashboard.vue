<script setup>
import { ref, onMounted } from 'vue'

const isCalling = ref(false)
const callStatus = ref('IDLE') // IDLE, DIALING, ACTIVE, HANGUP
const conversation = ref([
  { role: 'system', content: '等待连接...' }
])
const aiThinking = ref(false)

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

    <!-- 核心功能区：实时通话显示与群呼 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 通话控制与状态 (Bento 风格大卡片) -->
      <div class="lg:col-span-2 rounded-2xl border p-6 flex flex-col min-h-[400px]" 
        style="background: var(--bg-card); border-color: var(--border);">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full flex items-center justify-center bg-green-500/10 text-green-500" 
              v-if="callStatus === 'ACTIVE'">
              <svg class="w-6 h-6 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            </div>
            <div class="w-10 h-10 rounded-full flex items-center justify-center bg-gray-500/10 text-gray-500" v-else>
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-3.536 3.536m0 5.656L18.364 18.364m-5.656 0l-3.536-3.536m0-5.656L9.172 5.636M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-bold" style="color: var(--text-primary);">
                {{ callStatus === 'IDLE' ? '空闲中' : (callStatus === 'DIALING' ? '正在呼叫...' : '通话中: 138-xxxx-5678') }}
              </h3>
              <p class="text-xs" style="color: var(--text-muted);">系统实时状态监控</p>
            </div>
          </div>
          <div class="bg-black/20 px-3 py-1 rounded-full text-xs font-mono" style="color: var(--primary-light);">
            Latency: 450ms
          </div>
        </div>

        <!-- 实时对话流 -->
        <div class="flex-1 overflow-y-auto space-y-4 mb-6 pr-2 custom-scrollbar">
          <div v-for="(msg, idx) in conversation" :key="idx" 
            :class="['flex', msg.role === 'user' ? 'justify-start' : 'justify-end']">
            <div :class="['max-w-[80%] rounded-2xl px-4 py-2.5 text-sm shadow-sm', 
              msg.role === 'user' ? 'bg-zinc-800 text-white border border-white/5' : 'bg-blue-600 text-white rounded-tr-none']">
              {{ msg.content }}
            </div>
          </div>
          <!-- AI 思考动效 -->
          <div v-if="aiThinking" class="flex justify-end italic text-xs text-blue-400 animate-pulse">
            AI 正在组织话术...
          </div>
        </div>

        <div class="h-px w-full mb-6" style="background: var(--border);"></div>

        <div class="flex items-center gap-4">
          <button class="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-bold transition-all duration-300"
            :class="isCalling ? 'bg-red-500 hover:bg-red-600' : 'bg-green-600 hover:bg-green-700'"
            style="color: white;">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path v-if="!isCalling" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
            {{ isCalling ? '挂断通话' : '测试单呼' }}
          </button>
          <button class="w-14 h-14 rounded-xl flex items-center justify-center border transition-all duration-300"
            style="border-color: var(--border); color: var(--text-primary);"
            onmouseover="this.style.background='var(--bg-elevated)'"
            onmouseout="this.style.background='transparent'">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          </button>
        </div>
      </div>

      <!-- 右侧：实时任务动态 (小型列表) -->
      <div class="rounded-2xl border overflow-hidden flex flex-col" style="background: var(--bg-card); border-color: var(--border);">
        <div class="px-5 py-4 border-b flex items-center justify-between" style="border-color: var(--border);">
          <h3 class="text-sm font-semibold" style="color: var(--text-primary);">实时队列</h3>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-500 font-bold">LIVE</span>
        </div>
        <div class="flex-1 divide-y custom-scrollbar overflow-y-auto" style="border-color: var(--border);">
          <div v-for="(a, i) in activities" :key="i"
            class="px-5 py-4 transition-colors duration-150 cursor-pointer"
            onmouseover="this.style.background='var(--bg-elevated)'"
            onmouseout="this.style.background='transparent'"
          >
            <div class="flex items-center gap-3 mb-1">
              <div class="w-1.5 h-1.5 rounded-full shrink-0" :style="{ background: levelColors[a.level] }"></div>
              <span class="text-xs font-mono font-medium" style="color: var(--text-primary);">{{ a.phone }}</span>
            </div>
            <p class="text-[11px] leading-relaxed" style="color: var(--text-muted);">{{ a.text }}</p>
            <p class="text-[10px] mt-2 text-right opacity-50" style="color: var(--text-muted);">{{ a.time }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
