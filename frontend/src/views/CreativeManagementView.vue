<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useCreativeStore } from '@/stores/creative'
import axios from 'axios'

const API_BASE = '/api/v1'
const creativeStore = useCreativeStore()

const creatives = computed(() => creativeStore.creatives)
const selectedCreative = ref<any>(null)
const showDetailModal = ref(false)
const showPromptModal = ref(false)
const showAggregateModal = ref(false)
const showDeleteConfirm = ref(false)
const deleteTargetId = ref<string | null>(null)
const generatedPrompt = ref('')
const aggregateOutputFolder = ref('')
const loading = ref(false)
const aggregatingFiles = ref(false)

const selectedIds = ref<string[]>([])
const showBatchDeleteConfirm = ref(false)

const toggleSelection = (id: string) => {
  const index = selectedIds.value.indexOf(id)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(id)
  }
}

const isSelected = (id: string) => selectedIds.value.includes(id)

const selectAll = () => {
  if (selectedIds.value.length === creatives.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = creatives.value.map((c: any) => c.id)
  }
}

const handleViewCreative = (creative: any) => {
  selectedCreative.value = creative
  showDetailModal.value = true
}

const handleGeneratePrompt = async (creative: any) => {
  loading.value = true
  try {
    const response = await fetch(`${API_BASE}/prompts/generate-from-creative`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ creative_id: creative.id })
    })
    if (response.ok) {
      const data = await response.json()
      generatedPrompt.value = data.prompt
      creative.prompt = data.prompt
      showPromptModal.value = true
    }
  } catch (error) {
    console.error('Failed to generate prompt:', error)
  } finally {
    loading.value = false
  }
}

const confirmDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleDeleteCreative = async () => {
  if (!deleteTargetId.value) return
  showDeleteConfirm.value = false
  try {
    await fetch(`${API_BASE}/creatives/${deleteTargetId.value}`, { method: 'DELETE' })
    await creativeStore.fetchCreatives()
    selectedIds.value = selectedIds.value.filter(id => id !== deleteTargetId.value)
  } catch (error) {
    console.error('Failed to delete creative:', error)
  } finally {
    deleteTargetId.value = null
  }
}

const confirmBatchDelete = () => {
  if (selectedIds.value.length === 0) return
  showBatchDeleteConfirm.value = true
}

const handleBatchDelete = async () => {
  showBatchDeleteConfirm.value = false
  const idsToDelete = [...selectedIds.value]
  selectedIds.value = []
  
  for (const id of idsToDelete) {
    try {
      await fetch(`${API_BASE}/creatives/${id}`, { method: 'DELETE' })
    } catch (error) {
      console.error('Failed to delete creative:', error)
    }
  }
  await creativeStore.fetchCreatives()
}

const handleAggregateFiles = async () => {
  if (!selectedCreative.value || !aggregateOutputFolder.value) return
  
  aggregatingFiles.value = true
  try {
    const response = await axios.post(`${API_BASE}/creatives/aggregate-files`, {
      creative_id: selectedCreative.value.id,
      output_folder: aggregateOutputFolder.value
    })
    
    selectedCreative.value.aggregated_path = response.data.aggregated_path
    showAggregateModal.value = false
    alert(`成功聚合 ${response.data.files_count} 个文件到 ${response.data.aggregated_path}`)
  } catch (e: any) {
    console.error('Failed to aggregate files:', e)
    alert(e.response?.data?.detail || '聚合文件失败')
  } finally {
    aggregatingFiles.value = false
  }
}

const handleCopyPrompt = (prompt: string) => {
  navigator.clipboard.writeText(prompt).then(() => {
    alert('提示词已复制到剪贴板')
  }).catch(() => {
    alert('复制失败，请手动复制')
  })
}

onMounted(() => {
  creativeStore.fetchCreatives()
})
</script>

<template>
  <div class="p-6">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">创意管理</h1>
      <div class="flex gap-2">
        <button 
          v-if="selectedIds.length > 0"
          @click="confirmBatchDelete"
          class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          批量删除 ({{ selectedIds.length }})
        </button>
        <button 
          @click="selectAll"
          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          {{ selectedIds.length === creatives.length ? '取消全选' : '全选' }}
        </button>
      </div>
    </div>
    
    <div v-if="creatives.length === 0" class="text-center py-12 text-gray-500">
      <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
      <p class="text-lg">暂无创意</p>
      <p class="text-sm mt-2">前往"生成创意"页面创建你的第一个创意</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="creative in creatives" 
        :key="creative.id" 
        :class="[
          'bg-white rounded-lg shadow-sm border-2 p-6 hover:shadow-md transition-all cursor-pointer',
          isSelected(creative.id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
        ]"
        @click="toggleSelection(creative.id)"
      >
        <div class="flex items-start justify-between mb-2">
          <h3 class="font-semibold text-lg">{{ creative.title }}</h3>
          <div 
            :class="[
              'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0',
              isSelected(creative.id) ? 'bg-blue-500 border-blue-500' : 'border-gray-300'
            ]"
          >
            <svg v-if="isSelected(creative.id)" class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
        <p class="text-gray-600 text-sm mb-4 line-clamp-3">{{ creative.description }}</p>
        
        <div v-if="creative.key_points && creative.key_points.length > 0" class="mb-4">
          <p class="text-xs text-gray-500 mb-2">关键点:</p>
          <div class="flex flex-wrap gap-1">
            <span v-for="(point, idx) in creative.key_points.slice(0, 3)" :key="idx" class="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
              {{ point }}
            </span>
            <span v-if="creative.key_points.length > 3" class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
              +{{ creative.key_points.length - 3 }}
            </span>
          </div>
        </div>
        
        <div v-if="creative.aggregated_path" class="mb-3 p-2 bg-green-50 rounded-lg">
          <div class="flex items-center text-green-700 text-xs">
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <span>已聚合</span>
          </div>
        </div>

        <div class="text-xs text-gray-400 mb-4">
          创建时间: {{ new Date(creative.created_at).toLocaleString('zh-CN') }}
        </div>

        <div class="flex gap-2" @click.stop>
          <button @click="handleViewCreative(creative)" class="flex-1 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm">
            查看详情
          </button>
          <button @click="confirmDelete(creative.id)" class="px-3 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors text-sm">
            删除
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDetailModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showDetailModal = false">
      <div class="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4">
            <h2 class="text-xl font-bold">{{ selectedCreative.title }}</h2>
            <button @click="showDetailModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p class="text-gray-600 mb-6">{{ selectedCreative.description }}</p>
          
          <div v-if="selectedCreative.key_points && selectedCreative.key_points.length > 0" class="mb-6">
            <h3 class="font-semibold mb-2">关键点</h3>
            <ul class="list-disc list-inside space-y-1 text-gray-600">
              <li v-for="(point, idx) in selectedCreative.key_points" :key="idx">{{ point }}</li>
            </ul>
          </div>
          
          <div v-if="selectedCreative.prompt" class="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 class="font-semibold mb-2">生成的提示词</h3>
            <pre class="text-sm text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto">{{ selectedCreative.prompt }}</pre>
          </div>
          
          <div v-if="selectedCreative.aggregated_path" class="mb-4 p-3 bg-green-50 rounded-lg">
            <div class="flex items-center text-green-700">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <span class="text-sm">已聚合到: {{ selectedCreative.aggregated_path }}</span>
            </div>
          </div>
          
          <div class="flex flex-wrap gap-2 mb-6">
            <button 
              @click="handleGeneratePrompt(selectedCreative)"
              :disabled="loading"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              <span v-if="loading" class="flex items-center">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                生成中...
              </span>
              <span v-else>{{ selectedCreative.prompt ? '重新生成提示词' : '生成提示词' }}</span>
            </button>
            
            <button 
              @click="showAggregateModal = true"
              class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
            >
              聚合源文件
            </button>
            
            <button 
              v-if="selectedCreative.prompt"
              @click="handleCopyPrompt(selectedCreative.prompt)"
              class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              复制提示词
            </button>
          </div>

          <div v-if="selectedCreative.combination_id" class="text-sm text-gray-500">
            来源组合ID: {{ selectedCreative.combination_id }}
          </div>
        </div>
      </div>
    </div>

    <div v-if="showPromptModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showPromptModal = false">
      <div class="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4">
            <h2 class="text-xl font-bold">生成的提示词</h2>
            <button @click="showPromptModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <textarea v-model="generatedPrompt" readonly class="w-full h-64 p-3 border border-gray-300 rounded-lg text-sm resize-none" />
          <button @click="handleCopyPrompt(generatedPrompt)" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            复制提示词
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="showAggregateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">聚合源文件</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">目标文件夹路径</label>
            <input 
              v-model="aggregateOutputFolder" 
              type="text" 
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" 
              placeholder="例如: D:\projects\creative_output"
            />
          </div>
          <p class="text-xs text-gray-500">
            将把该创意相关的所有源文件复制到指定文件夹中，按文件类型分类存放。
          </p>
          <div class="flex justify-end space-x-3">
            <button @click="showAggregateModal = false" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">取消</button>
            <button 
              @click="handleAggregateFiles" 
              :disabled="!aggregateOutputFolder || aggregatingFiles"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <span v-if="aggregatingFiles" class="flex items-center">
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                聚合中...
              </span>
              <span v-else>开始聚合</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">确认删除</h3>
        <p class="text-gray-600 mb-6">确定要删除这个创意吗？此操作不可撤销。</p>
        <div class="flex justify-end space-x-3">
          <button @click="showDeleteConfirm = false; deleteTargetId = null" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">取消</button>
          <button @click="handleDeleteCreative" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">删除</button>
        </div>
      </div>
    </div>
    
    <div v-if="showBatchDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">确认批量删除</h3>
        <p class="text-gray-600 mb-6">确定要删除选中的 {{ selectedIds.length }} 个创意吗？此操作不可撤销。</p>
        <div class="flex justify-end space-x-3">
          <button @click="showBatchDeleteConfirm = false" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">取消</button>
          <button @click="handleBatchDelete" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>
