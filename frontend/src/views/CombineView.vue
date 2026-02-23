<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useInspirationStore } from '@/stores/inspiration'
import { useCombinationStore } from '@/stores/combination'
import type { Inspiration, CustomRelationType, InspirationRelation } from '@/types'
import axios from 'axios'
import TopologyGraph from '@/components/TopologyGraph.vue'

const API_BASE = '/api/v1'

const inspirationStore = useInspirationStore()
const combinationStore = useCombinationStore()

const selectedInspirations = ref<string[]>([])
const combinationName = ref('')
const combinationDescription = ref('')
const showRelationModal = ref(false)
const showRelationTypeModal = ref(false)
const showEdgeDetailModal = ref(false)
const currentRelation = ref<{
  sourceId: string
  targetId: string
  type: string
  customTypeId: string | null
  description: string
} | null>(null)

const selectedEdge = ref<any>(null)

const relationTypes = ref<CustomRelationType[]>([])
const newRelationType = ref({
  name: '',
  display_name: '',
  description: '',
  style: {
    stroke: '#6b7280',
    strokeWidth: 2,
    markerEnd: '',
    markerStart: ''
  }
})

const aiCompleting = ref(false)
const aiCompleteStatus = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const aiCompleteMessage = ref('')

const topologyNodes = computed(() => {
  return selectedInspirations.value.map((id) => {
    const insp = inspirationStore.getInspiration(id)
    if (!insp) return null
    
    const index = selectedInspirations.value.indexOf(id)
    const row = Math.floor(index / 3)
    const col = index % 3
    
    return {
      id: id,
      name: insp.name,
      type: insp.type,
      x: col * 200 + 120,
      y: row * 120 + 80
    }
  }).filter(Boolean)
})

const topologyEdges = computed(() => {
  return combinationStore.currentRelations.map(rel => ({
    id: rel.id || `${rel.source_id}-${rel.target_id}`,
    sourceId: rel.source_id,
    targetId: rel.target_id,
    relationType: rel.relation_type,
    description: rel.description || '',
    customTypeId: rel.custom_type_id
  }))
})

const toggleSelection = (id: string) => {
  const index = selectedInspirations.value.indexOf(id)
  if (index > -1) {
    selectedInspirations.value.splice(index, 1)
  } else {
    selectedInspirations.value.push(id)
  }
}

const isSelected = (id: string) => selectedInspirations.value.includes(id)

const handleCreateRelation = (sourceId: string, targetId: string) => {
  currentRelation.value = {
    sourceId,
    targetId,
    type: 'parallel',
    customTypeId: null,
    description: ''
  }
  showRelationModal.value = true
}

const handleSelectEdge = (edge: any) => {
  selectedEdge.value = edge
  showEdgeDetailModal.value = true
}

const handleAddRelation = () => {
  if (currentRelation.value) {
    combinationStore.addRelation({
      id: `rel-${Date.now()}`,
      source_id: currentRelation.value.sourceId,
      target_id: currentRelation.value.targetId,
      relation_type: currentRelation.value.type as any,
      custom_type_id: currentRelation.value.customTypeId,
      description: currentRelation.value.description,
      created_at: new Date().toISOString()
    })
  }
  showRelationModal.value = false
  currentRelation.value = null
}

const handleUpdateEdgeDescription = () => {
  if (selectedEdge.value) {
    const rel = combinationStore.currentRelations.find(r => r.id === selectedEdge.value.id)
    if (rel) {
      rel.description = selectedEdge.value.description
    }
  }
  showEdgeDetailModal.value = false
  selectedEdge.value = null
}

const handleDeleteEdge = () => {
  if (selectedEdge.value) {
    combinationStore.removeRelation(selectedEdge.value.id)
  }
  showEdgeDetailModal.value = false
  selectedEdge.value = null
}

const handleCreateCombination = async () => {
  if (!combinationName.value || selectedInspirations.value.length < 2) return
  
  try {
    const combination = await combinationStore.createCombination({
      name: combinationName.value,
      description: combinationDescription.value || undefined,
      inspiration_ids: selectedInspirations.value,
      relations: combinationStore.currentRelations
    })
    combinationStore.setCurrentCombination(combination)
    aiCompleteStatus.value = 'idle'
    aiCompleteMessage.value = ''
    alert('组合创建成功！')
  } catch (error) {
    console.error('Failed to create combination:', error)
    alert('创建组合失败')
  }
}

const handleClearCombination = () => {
  selectedInspirations.value = []
  combinationName.value = ''
  combinationDescription.value = ''
  combinationStore.clearCurrent()
  aiCompleteStatus.value = 'idle'
  aiCompleteMessage.value = ''
}

const handleAICompleteRelations = async () => {
  if (selectedInspirations.value.length < 2) return
  
  aiCompleting.value = true
  aiCompleteStatus.value = 'loading'
  aiCompleteMessage.value = 'AI正在分析灵感内容并生成关系...'
  
  try {
    const response = await axios.post(`${API_BASE}/inspirations/ai-complete-relations`, {
      inspiration_ids: selectedInspirations.value,
      existing_relations: combinationStore.currentRelations
    })
    
    const newRelations = response.data.relations || []
    
    for (const rel of newRelations) {
      const exists = combinationStore.currentRelations.some(
        r => (r.source_id === rel.source_id && r.target_id === rel.target_id) ||
             (r.source_id === rel.target_id && r.target_id === rel.source_id)
      )
      if (!exists) {
        combinationStore.addRelation({
          id: `rel-ai-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          source_id: rel.source_id,
          target_id: rel.target_id,
          relation_type: rel.relation_type,
          description: rel.description,
          created_at: new Date().toISOString()
        })
      }
    }
    
    aiCompleteStatus.value = 'success'
    aiCompleteMessage.value = `AI成功生成 ${newRelations.length} 个关系！`
    
    setTimeout(() => {
      aiCompleteStatus.value = 'idle'
    }, 3000)
  } catch (error: any) {
    aiCompleteStatus.value = 'error'
    aiCompleteMessage.value = error.response?.data?.detail || 'AI补全关系失败，请检查AI模型配置'
    console.error('Failed to AI complete relations:', error)
  } finally {
    aiCompleting.value = false
  }
}

const fetchRelationTypes = async () => {
  try {
    const response = await axios.get(`${API_BASE}/relation-types`)
    relationTypes.value = response.data
  } catch (error) {
    console.error('Failed to fetch relation types:', error)
  }
}

const handleAddRelationType = async () => {
  if (!newRelationType.value.name || !newRelationType.value.display_name) return
  
  try {
    const response = await axios.post(`${API_BASE}/relation-types`, newRelationType.value)
    relationTypes.value.push(response.data)
    showRelationTypeModal.value = false
    newRelationType.value = {
      name: '',
      display_name: '',
      description: '',
      style: {
        stroke: '#6b7280',
        strokeWidth: 2,
        markerEnd: '',
        markerStart: ''
      }
    }
  } catch (error) {
    console.error('Failed to add relation type:', error)
  }
}

onMounted(async () => {
  await Promise.all([
    fetchRelationTypes(),
    inspirationStore.fetchInspirations(),
    combinationStore.fetchCombinations()
  ])
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">生成组合</h1>
      <div class="flex space-x-3">
        <button 
          @click="handleClearCombination"
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
        >
          清空选择
        </button>
        <button 
          @click="showRelationTypeModal = true"
          class="px-4 py-2 border border-purple-300 rounded-lg text-purple-700 hover:bg-purple-50 transition-colors"
        >
          管理关系类型
        </button>
        <button 
          @click="handleAICompleteRelations"
          :disabled="selectedInspirations.length < 2 || aiCompleting"
          class="px-4 py-2 border border-blue-300 rounded-lg text-blue-700 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="aiCompleting" class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            AI分析中...
          </span>
          <span v-else class="flex items-center">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            AI补全关系
          </span>
        </button>
        <button 
          @click="handleCreateCombination"
          :disabled="selectedInspirations.length < 2 || !combinationName"
          class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          创建组合
        </button>
      </div>
    </div>
    
    <div v-if="aiCompleteStatus !== 'idle'" class="p-4 rounded-lg" :class="{
      'bg-blue-50 text-blue-700': aiCompleteStatus === 'loading',
      'bg-green-50 text-green-700': aiCompleteStatus === 'success',
      'bg-red-50 text-red-700': aiCompleteStatus === 'error'
    }">
      <div class="flex items-center">
        <svg v-if="aiCompleteStatus === 'loading'" class="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg v-else-if="aiCompleteStatus === 'success'" class="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <svg v-else-if="aiCompleteStatus === 'error'" class="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        {{ aiCompleteMessage }}
      </div>
    </div>
    
    <div class="grid grid-cols-12 gap-6">
      <div class="col-span-4 bg-white rounded-lg shadow-md p-4">
        <h2 class="text-lg font-semibold mb-4">选择灵感</h2>
        <input 
          v-model="combinationName" 
          type="text" 
          placeholder="组合名称 *" 
          class="input-field mb-2"
        />
        <input 
          v-model="combinationDescription" 
          type="text" 
          placeholder="组合描述（可选）" 
          class="input-field mb-4"
        />
        
        <div class="space-y-2 max-h-72 overflow-y-auto">
          <div 
            v-for="insp in inspirationStore.inspirations" 
            :key="insp.id"
            @click="toggleSelection(insp.id)"
            :class="[
              'p-3 rounded-lg border cursor-pointer transition-all',
              isSelected(insp.id) 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-gray-200 hover:border-gray-300'
            ]"
          >
            <div class="flex justify-between items-center">
              <span class="font-medium">{{ insp.name }}</span>
              <span v-if="isSelected(insp.id)" class="text-primary-600">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
              </span>
            </div>
            <div class="text-sm text-gray-500 mt-1">{{ insp.type }}</div>
          </div>
          <div v-if="inspirationStore.inspirations.length === 0" class="text-center py-4 text-gray-400">
            还没有灵感，请先添加
          </div>
        </div>
        
        <div v-if="selectedInspirations.length > 0" class="mt-4 pt-4 border-t">
          <h3 class="text-sm font-medium text-gray-700 mb-2">已选择 {{ selectedInspirations.length }} 个灵感</h3>
          <p class="text-xs text-gray-500">点击节点创建关系</p>
          <p class="text-xs text-gray-400 mt-1">点击连线可编辑关系描述</p>
          <p class="text-xs text-blue-500 mt-1">或使用"AI补全关系"自动生成</p>
        </div>
        
        <div v-if="combinationStore.currentCombination" class="mt-4 pt-4 border-t">
          <h3 class="text-sm font-medium text-green-700 mb-2">
            当前组合: {{ combinationStore.currentCombination.name }}
          </h3>
          <p class="text-xs text-gray-500">
            关系数: {{ combinationStore.currentRelations.length }}
          </p>
        </div>
      </div>
      
      <div class="col-span-8 bg-white rounded-lg shadow-md p-4">
        <h2 class="text-lg font-semibold mb-4">可视化组合</h2>
        <div class="h-96 border border-gray-200 rounded-lg overflow-hidden">
          <TopologyGraph 
            v-if="topologyNodes.length > 0"
            :nodes="topologyNodes" 
            :edges="topologyEdges"
            :custom-relation-types="relationTypes"
            :editable="true"
            :height="384"
            @create-relation="handleCreateRelation"
            @select-edge="handleSelectEdge"
          />
          <div v-else class="h-full flex items-center justify-center text-gray-400">
            <div class="text-center">
              <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <p>从左侧选择灵感开始组合</p>
            </div>
          </div>
        </div>
        
        <div class="mt-4 flex items-center space-x-4 text-sm text-gray-500">
          <div class="flex items-center">
            <div class="w-8 h-0.5 bg-purple-500 mr-2"></div>
            <span>主从关系</span>
          </div>
          <div class="flex items-center">
            <div class="w-8 h-0.5 bg-green-500 mr-2"></div>
            <span>平行关系</span>
          </div>
          <div class="flex items-center">
            <div class="w-8 h-0.5 bg-red-500 mr-2"></div>
            <span>对比关系</span>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showRelationModal && currentRelation" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">定义关系</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">关系类型</label>
            <select v-model="currentRelation.type" class="input-field">
              <option value="primary">主从关系（箭头）</option>
              <option value="parallel">平行关系（连线）</option>
              <option value="contrast">对比关系（双箭头）</option>
              <option v-for="rt in relationTypes.filter(r => r.name !== 'primary' && r.name !== 'parallel' && r.name !== 'contrast')" :key="rt.id" :value="rt.id">
                {{ rt.display_name }}（自定义）
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">描述（可选）</label>
            <input v-model="currentRelation.description" type="text" class="input-field" placeholder="描述这个关系..." />
          </div>
          <div class="flex justify-end space-x-3">
            <button @click="showRelationModal = false; currentRelation = null" class="btn-secondary">取消</button>
            <button @click="handleAddRelation" class="btn-primary">确认</button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showRelationTypeModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-[500px] max-h-[80vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">管理关系类型</h3>
        
        <div class="mb-6">
          <h4 class="text-sm font-medium text-gray-700 mb-2">已有关系类型</h4>
          <div class="space-y-2">
            <div v-for="rt in relationTypes" :key="rt.id" class="p-3 border rounded-lg flex justify-between items-center">
              <div>
                <span class="font-medium">{{ rt.display_name }}</span>
                <span class="text-xs text-gray-500 ml-2">({{ rt.name }})</span>
                <p v-if="rt.description" class="text-xs text-gray-500 mt-1">{{ rt.description }}</p>
              </div>
              <div class="w-8 h-1 rounded" :style="{ backgroundColor: rt.style?.stroke || '#6b7280' }"></div>
            </div>
          </div>
        </div>
        
        <div class="border-t pt-4">
          <h4 class="text-sm font-medium text-gray-700 mb-2">添加自定义关系类型</h4>
          <div class="space-y-3">
            <input 
              v-model="newRelationType.name" 
              type="text" 
              placeholder="类型名称（英文）" 
              class="input-field"
            />
            <input 
              v-model="newRelationType.display_name" 
              type="text" 
              placeholder="显示名称" 
              class="input-field"
            />
            <input 
              v-model="newRelationType.description" 
              type="text" 
              placeholder="描述（可选）" 
              class="input-field"
            />
            <div class="flex items-center space-x-4">
              <div class="flex-1">
                <label class="block text-xs text-gray-500 mb-1">线条颜色</label>
                <input 
                  v-model="newRelationType.style.stroke" 
                  type="color" 
                  class="w-full h-8 rounded cursor-pointer"
                />
              </div>
              <div class="flex-1">
                <label class="block text-xs text-gray-500 mb-1">线条宽度</label>
                <input 
                  v-model.number="newRelationType.style.strokeWidth" 
                  type="number" 
                  min="1" 
                  max="5" 
                  class="input-field"
                />
              </div>
            </div>
            <div class="flex items-center space-x-4">
              <label class="flex items-center">
                <input v-model="newRelationType.style.markerEnd" type="checkbox" true-value="arrow" false-value="" class="mr-2" />
                <span class="text-sm">终点箭头</span>
              </label>
              <label class="flex items-center">
                <input v-model="newRelationType.style.markerStart" type="checkbox" true-value="arrow" false-value="" class="mr-2" />
                <span class="text-sm">起点箭头</span>
              </label>
            </div>
            <div class="flex justify-end space-x-3">
              <button @click="showRelationTypeModal = false" class="btn-secondary">关闭</button>
              <button @click="handleAddRelationType" class="btn-primary" :disabled="!newRelationType.name || !newRelationType.display_name">添加</button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="showEdgeDetailModal && selectedEdge" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">编辑关系</h3>
        <div class="space-y-4">
          <div class="p-3 bg-gray-50 rounded-lg">
            <p class="text-sm text-gray-600">
              关系类型: {{ selectedEdge.relationType }}
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">关系描述</label>
            <textarea 
              v-model="selectedEdge.description" 
              class="input-field h-24" 
              placeholder="描述这个关系的具体含义..."
            ></textarea>
          </div>
          <div class="flex justify-between space-x-3">
            <button @click="handleDeleteEdge" class="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors">
              删除关系
            </button>
            <div class="flex space-x-3">
              <button @click="showEdgeDetailModal = false" class="btn-secondary">取消</button>
              <button @click="handleUpdateEdgeDescription" class="btn-primary">保存</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
