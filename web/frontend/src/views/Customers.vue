<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const customers = ref([])
const loading = ref(true)
const showAddModal = ref(false)

const newCustomer = ref({ name: '', phone: '', remark: '' })

const statusColors = {
  '待跟进': { bg: '#3B82F620', text: '#60A5FA' },
  '高意向': { bg: '#22C55E20', text: '#22C55E' },
  '拒绝':   { bg: '#EF444420', text: '#EF4444' },
  '无效号码': { bg: '#64748B20', text: '#94A3B8' }
}

const fetchCustomers = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/customers/')
    customers.value = res.data
  } catch (e) {
    console.error('加载失败', e)
  } finally {
    loading.value = false
  }
}

const submitCustomer = async () => {
  try {
    await axios.post('http://127.0.0.1:8000/api/customers/', newCustomer.value)
    showAddModal.value = false
    newCustomer.value = { name: '', phone: '', remark: '' }
    fetchCustomers()
  } catch (e) {
    alert(e.response?.data?.detail || '添加失败')
  }
}

onMounted(fetchCustomers)
</script>

<template>
  <div class="space-y-5">
    <!-- 头部 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold" style="color: var(--text-primary);">客户管理</h1>
        <p class="text-sm mt-1" style="color: var(--text-muted);">管理线索号码池，选中即可交由 AI 发起外呼</p>
      </div>
      <div class="flex gap-3">
        <button class="px-4 py-2 rounded-lg text-sm font-medium cursor-pointer border transition-colors duration-200"
          style="background: var(--bg-card); border-color: var(--border); color: var(--text-secondary);"
          onmouseover="this.style.borderColor='var(--primary)'"
          onmouseout="this.style.borderColor='var(--border)'"
        >导入 CSV</button>
        <button @click="showAddModal = true"
          class="px-4 py-2 rounded-lg text-sm font-medium text-white cursor-pointer transition-all duration-200 hover:opacity-90"
          style="background: var(--primary);">
          + 添加客户
        </button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="rounded-xl border overflow-hidden" style="background: var(--bg-card); border-color: var(--border);">
      <div class="px-5 py-3 border-b" style="border-color: var(--border);">
        <input type="text" placeholder="搜索姓名或手机号..."
          class="w-full max-w-sm px-3 py-2 rounded-lg text-sm outline-none border transition-colors duration-200"
          style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-primary);"
          onfocus="this.style.borderColor='var(--primary)'"
          onblur="this.style.borderColor='var(--border)'" />
      </div>

      <!-- 表格 -->
      <table class="w-full">
        <thead>
          <tr style="border-bottom: 1px solid var(--border);">
            <th class="text-left text-xs font-medium py-3 px-5" style="color: var(--text-muted);">姓名</th>
            <th class="text-left text-xs font-medium py-3 px-5" style="color: var(--text-muted);">手机号码</th>
            <th class="text-left text-xs font-medium py-3 px-5" style="color: var(--text-muted);">意向状态</th>
            <th class="text-left text-xs font-medium py-3 px-5" style="color: var(--text-muted);">备注</th>
            <th class="text-right text-xs font-medium py-3 px-5" style="color: var(--text-muted);">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="py-16 text-center text-sm" style="color: var(--text-muted);">数据加载中...</td>
          </tr>
          <tr v-else-if="customers.length === 0">
            <td colspan="5" class="py-16 text-center">
              <svg class="w-12 h-12 mx-auto mb-3" style="color: var(--text-muted);" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
              </svg>
              <p class="text-sm" style="color: var(--text-muted);">暂无客户，请添加或导入线索</p>
            </td>
          </tr>
          <tr v-for="p in customers" :key="p.id"
            class="transition-colors duration-150 cursor-pointer"
            style="border-bottom: 1px solid var(--border);"
            onmouseover="this.style.background='var(--bg-elevated)'"
            onmouseout="this.style.background='transparent'"
          >
            <td class="py-3.5 px-5 text-sm font-medium" style="color: var(--text-primary);">{{ p.name }}</td>
            <td class="py-3.5 px-5 text-sm font-mono" style="color: var(--text-secondary);">{{ p.phone }}</td>
            <td class="py-3.5 px-5">
              <span class="text-xs font-medium px-2 py-1 rounded-md"
                :style="{ background: (statusColors[p.status]||statusColors['待跟进']).bg, color: (statusColors[p.status]||statusColors['待跟进']).text }">
                {{ p.status }}
              </span>
            </td>
            <td class="py-3.5 px-5 text-sm max-w-[200px] truncate" style="color: var(--text-muted);" :title="p.remark">{{ p.remark || '-' }}</td>
            <td class="py-3.5 px-5 text-right">
              <button class="text-xs font-medium px-2.5 py-1 rounded-md cursor-pointer transition-colors mr-2"
                style="background: #22C55E20; color: #22C55E;">AI 外呼</button>
              <button class="text-xs font-medium px-2.5 py-1 rounded-md cursor-pointer transition-colors"
                style="background: var(--bg-elevated); color: var(--text-secondary);">详情</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 添加客户弹窗 -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0" style="background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);" @click="showAddModal = false"></div>
      <div class="relative w-full max-w-md mx-4 rounded-xl p-6 border" style="background: var(--bg-card); border-color: var(--border);">
        <h3 class="text-lg font-semibold mb-5" style="color: var(--text-primary);">添加客户</h3>
        <div class="space-y-4">
          <input v-model="newCustomer.name" placeholder="客户姓名"
            class="w-full px-3 py-2.5 rounded-lg text-sm outline-none border transition-colors"
            style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-primary);"
            onfocus="this.style.borderColor='var(--primary)'" onblur="this.style.borderColor='var(--border)'" />
          <input v-model="newCustomer.phone" placeholder="手机号码"
            class="w-full px-3 py-2.5 rounded-lg text-sm outline-none border transition-colors"
            style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-primary);"
            onfocus="this.style.borderColor='var(--primary)'" onblur="this.style.borderColor='var(--border)'" />
          <textarea v-model="newCustomer.remark" placeholder="备注信息（选填）" rows="3"
            class="w-full px-3 py-2.5 rounded-lg text-sm outline-none border transition-colors resize-none"
            style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-primary);"
            onfocus="this.style.borderColor='var(--primary)'" onblur="this.style.borderColor='var(--border)'"></textarea>
        </div>
        <div class="flex gap-3 mt-5">
          <button @click="showAddModal = false"
            class="flex-1 py-2.5 rounded-lg text-sm font-medium cursor-pointer border transition-colors"
            style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-secondary);">取消</button>
          <button @click="submitCustomer"
            class="flex-1 py-2.5 rounded-lg text-sm font-medium text-white cursor-pointer transition-all hover:opacity-90"
            style="background: var(--primary);">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
