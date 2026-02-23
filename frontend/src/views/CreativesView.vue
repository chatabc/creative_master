<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useCombinationStore } from '@/stores/combination'
import { useInspirationStore } from '@/stores/inspiration'
import type { InspirationRelation, Creative } from '@/types'
import axios from 'axios'
import TopologyGraph from '@/components/TopologyGraph.vue'

const API_BASE = '/api/v1'
const route = useRoute()

const combinationStore = useCombinationStore()
const inspirationStore = useInspirationStore()

type Step = 'select' | 'topologies' | 'edit' | 'generating' | 'results'

const step = ref<Step>('select')
const selectedCombinationId = ref<string>('')
const loading = ref(false)
const error = ref('')

const topologies = ref<any[]>([])
const selectedTopologyIndex = ref<number>(0)

const currentNodes = ref<any[]>([])
const currentEdges = ref<any[]>([])
const currentRelations = ref<InspirationRelation[]>([])

const generatedCreatives = ref<Creative[]>([])
const selectedCreative = ref<Creative | null>(null)

const customRelationTypes = ref<any[]>([])

const showRelationModal = ref(false)
const currentRelation = ref<{
  sourceId: string
  targetId: string
  type: string
  customTypeId: string | null
  description: string
} | null>(null)

const showEdgeDetailModal = ref(false)
const selectedEdge = ref<any>(null)

const generatingPrompt = ref(false)
const showAggregateModal = ref(false)
const aggregateOutputFolder = ref('')
const aggregatingFiles = ref(false)

const combinations = computed(() => combinationStore.combinations)

function getNodeColor(type: string): string {
  const colors: Record<string, string> = {
    image: '#3b82f6',
    code: '#22c55e',
    text: '#eab308',
    video: '#ef4444',
    audio: '#a855f7',
    document: '#ec4899',
    folder: '#6b7280'
  }
  return colors[type] || '#6b7280'
}

const handleSelectCombination = async () => {
  if (!selectedCombinationId.value) return
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await axios.get(`${API_BASE}/combinations/${selectedCombinationId.value}`)
    const combination = response.data
    
    await generateTopologies(combination)
    
    step.value = 'topologies'
  } catch (e: any) {
    error.value = e.response?.data?.detail || '加载组合失败'
    console.error('Failed to load combination:', e)
  } finally {
    loading.value = false
  }
}

const generateTopologies = async (combination: any) => {
  const inspirationIds = combination.inspirations || combination.inspiration_ids || []
  
  const inspirations = await Promise.all(
    inspirationIds.map((id: string) => 
      axios.get(`${API_BASE}/inspirations/${id}`)
    )
  )
  
  const baseNodes = inspirations.map((resp, index) => {
    const insp = resp.data
    const row = Math.floor(index / 3)
    const col = index % 3
    
    return {
      id: insp.id,
      name: insp.name,
      type: insp.type,
      x: col * 200 + 120,
      y: row * 120 + 80
    }
  })
  
  const baseEdges = (combination.relations || []).map((rel: InspirationRelation) => ({
    id: rel.id || `${rel.source_id}-${rel.target_id}`,
    sourceId: rel.source_id,
    targetId: rel.target_id,
    relationType: rel.relation_type,
    description: rel.description || '',
    customTypeId: rel.custom_type_id
  }))
  
  topologies.value = [
    {
      id: 'original',
      name: '原本拓扑图',
      description: '基于组合原始关系生成的拓扑图',
      nodes: JSON.parse(JSON.stringify(baseNodes)),
      edges: JSON.parse(JSON.stringify(baseEdges)),
      relations: JSON.parse(JSON.stringify(combination.relations || []))
    }
  ]
  
  try {
    const response = await axios.post(`${API_BASE}/topologies/generate-variants`, {
      combination_id: selectedCombinationId.value,
      base_nodes: baseNodes,
      base_edges: baseEdges,
      base_relations: combination.relations || []
    })
    
    if (response.data && response.data.length >= 2) {
      topologies.value.push({
        id: 'extended-1',
        name: '扩展拓扑图 1',
        description: 'AI分析生成的扩展关系变体',
        nodes: JSON.parse(JSON.stringify(response.data[0].nodes)),
        edges: JSON.parse(JSON.stringify(response.data[0].edges)),
        relations: JSON.parse(JSON.stringify(response.data[0].relations))
      })
      
      topologies.value.push({
        id: 'extended-2',
        name: '扩展拓扑图 2',
        description: 'AI分析生成的另一种关系变体',
        nodes: JSON.parse(JSON.stringify(response.data[1].nodes)),
        edges: JSON.parse(JSON.stringify(response.data[1].edges)),
        relations: JSON.parse(JSON.stringify(response.data[1].relations))
      })
    }
  } catch (e) {
    console.error('Failed to generate AI topologies:', e)
    
    const extendedNodes1 = JSON.parse(JSON.stringify(baseNodes))
    extendedNodes1.forEach((node: any, index: number) => {
      node.x = (index % 3) * 220 + 130
      node.y = Math.floor(index / 3) * 140 + 90
    })
    
    const extendedNodes2 = JSON.parse(JSON.stringify(baseNodes))
    extendedNodes2.forEach((node: any, index: number) => {
      const angle = (index / extendedNodes2.length) * 2 * Math.PI - Math.PI / 2
      const radius = 150
      node.x = 250 + Math.cos(angle) * radius
      node.y = 180 + Math.sin(angle) * radius
    })
    
    const extendedEdges1 = [...baseEdges]
    const extendedEdges2 = [...baseEdges]
    
    if (baseNodes.length >= 2) {
      extendedEdges1.push({
        id: `new-${Date.now()}`,
        sourceId: baseNodes[0].id,
        targetId: baseNodes[baseNodes.length - 1].id,
        relationType: 'parallel',
        description: '间接关联',
        customTypeId: null
      })
    }
    
    if (baseNodes.length >= 3) {
      extendedEdges2.push({
        id: `new-${Date.now()}`,
        sourceId: baseNodes[1].id,
        targetId: baseNodes[2].id,
        relationType: 'parallel',
        description: '互补关系',
        customTypeId: null
      })
    }
    
    topologies.value.push({
      id: 'extended-1',
      name: '扩展拓扑图 1',
      description: '在原本基础上添加新的关系连接',
      nodes: extendedNodes1,
      edges: extendedEdges1,
      relations: [...(combination.relations || []), {
        id: `new-${Date.now()}`,
        source_id: baseNodes[0]?.id,
        target_id: baseNodes[baseNodes.length - 1]?.id,
        relation_type: 'parallel',
        description: '间接关联'
      }]
    })
    
    topologies.value.push({
      id: 'extended-2',
      name: '扩展拓扑图 2',
      description: '重新排列节点位置和关系',
      nodes: extendedNodes2,
      edges: extendedEdges2,
      relations: [...(combination.relations || []), {
        id: `new-${Date.now()}`,
        source_id: baseNodes[1]?.id,
        target_id: baseNodes[2]?.id,
        relation_type: 'parallel',
        description: '互补关系'
      }]
    })
  }
}

const handleSelectTopology = (index: number) => {
  selectedTopologyIndex.value = index
  const topology = topologies.value[index]
  
  currentNodes.value = JSON.parse(JSON.stringify(topology.nodes))
  currentEdges.value = JSON.parse(JSON.stringify(topology.edges))
  currentRelations.value = JSON.parse(JSON.stringify(topology.relations))
  
  step.value = 'edit'
}

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

const handleAddRelation = () => {
  if (currentRelation.value) {
    const newRel: InspirationRelation = {
      id: `rel-${Date.now()}`,
      source_id: currentRelation.value.sourceId,
      target_id: currentRelation.value.targetId,
      relation_type: currentRelation.value.type as any,
      custom_type_id: currentRelation.value.customTypeId,
      description: currentRelation.value.description,
      created_at: new Date().toISOString()
    }
    
    currentRelations.value.push(newRel)
    currentEdges.value.push({
      id: newRel.id,
      sourceId: newRel.source_id,
      targetId: newRel.target_id,
      relationType: newRel.relation_type,
      description: newRel.description || '',
      customTypeId: newRel.custom_type_id
    })
  }
  showRelationModal.value = false
  currentRelation.value = null
}

const handleSelectEdge = (edge: any) => {
  selectedEdge.value = edge
  showEdgeDetailModal.value = true
}

const handleUpdateEdgeDescription = () => {
  if (selectedEdge.value) {
    const relIndex = currentRelations.value.findIndex(r => r.id === selectedEdge.value.id)
    if (relIndex > -1) {
      currentRelations.value[relIndex].description = selectedEdge.value.description
    }
    const edgeIndex = currentEdges.value.findIndex(e => e.id === selectedEdge.value.id)
    if (edgeIndex > -1) {
      currentEdges.value[edgeIndex].description = selectedEdge.value.description
    }
  }
  showEdgeDetailModal.value = false
  selectedEdge.value = null
}

const handleDeleteEdge = () => {
  if (selectedEdge.value) {
    currentRelations.value = currentRelations.value.filter(r => r.id !== selectedEdge.value.id)
    currentEdges.value = currentEdges.value.filter(e => e.id !== selectedEdge.value.id)
  }
  showEdgeDetailModal.value = false
  selectedEdge.value = null
}

const handleGenerateCreatives = async () => {
  if (!selectedCombinationId.value) return
  
  loading.value = true
  error.value = ''
  step.value = 'generating'
  
  try {
    const response = await axios.post(`${API_BASE}/creatives/generate`, {
      combination_id: selectedCombinationId.value,
      relations: currentRelations.value
    })
    
    generatedCreatives.value = response.data || []
    step.value = 'results'
  } catch (e: any) {
    error.value = e.response?.data?.detail || '生成创意失败，请检查AI模型配置'
    console.error('Failed to generate creatives:', e)
    step.value = 'edit'
  } finally {
    loading.value = false
  }
}

const handleViewCreative = (creative: Creative) => {
  selectedCreative.value = creative
}

const handleReset = () => {
  step.value = 'select'
  selectedCombinationId.value = ''
  topologies.value = []
  selectedTopologyIndex.value = 0
  currentNodes.value = []
  currentEdges.value = []
  currentRelations.value = []
  generatedCreatives.value = []
  selectedCreative.value = null
  error.value = ''
}

const fetchRelationTypes = async () => {
  try {
    const response = await axios.get(`${API_BASE}/relation-types`)
    customRelationTypes.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch relation types:', error)
  }
}

const handleGeneratePrompt = async (creative: Creative) => {
  generatingPrompt.value = true
  try {
    const response = await axios.post(`${API_BASE}/prompts/generate-from-creative`, {
      creative_id: creative.id,
      regenerate: !!creative.prompt
    })
    
    creative.prompt = response.data.prompt
    if (response.data.aggregated_path) {
      creative.aggregated_path = response.data.aggregated_path
    }
  } catch (e: any) {
    console.error('Failed to generate prompt:', e)
    alert(e.response?.data?.detail || '生成提示词失败')
  } finally {
    generatingPrompt.value = false
  }
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

onMounted(async () => {
  await Promise.all([
    inspirationStore.fetchInspirations(),
    combinationStore.fetchCombinations(),
    fetchRelationTypes()
  ])
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">生成创意</h1>
        <p class="text-gray-500 mt-1">选择组合，生成拓扑图变体，创建创意方案</p>
      </div>
      
      <button 
        @click="handleReset"
        v-if="step !== 'select'"
        class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
      >
        重新开始
      </button>
    </div>
    
    <div v-if="error" class="p-4 bg-red-50 text-red-700 rounded-lg">
      {{ error }}
    </div>
    
    <div v-if="step === 'select'" class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-lg font-semibold mb-4">选择组合</h2>
      
      <div v-if="combinations.length === 0" class="text-center py-12 text-gray-500">
        <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 012 2v6a2 2 012 2m-4 2a2 2 011.586 7.707 9.293a1 1 0 001.414 1.414L9 10.586 7.707 9.293z" />
        </svg>
        <p class="text-lg">还没有组合</p>
        <p class="text-sm mt-2">前往"生成组合"页面创建你的第一个组合</p>
        <button @click="$router.push('/combine')" class="btn-primary mt-4">
          去创建组合
        </button>
      </div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div 
          v-for="combo in combinations" 
          :key="combo.id"
          @click="selectedCombinationId = combo.id"
          :class="[
            'p-4 rounded-lg border-2 cursor-pointer transition-all',
            selectedCombinationId === combo.id 
              ? 'border-primary-500 bg-primary-50' 
              : 'border-gray-200 hover:border-gray-300'
          ]"
        >
          <h3 class="font-semibold text-lg mb-2">{{ combo.name }}</h3>
          <p class="text-sm text-gray-600 line-clamp-2 mb-2">{{ combo.description || '暂无描述' }}</p>
          <div class="text-xs text-gray-500">
            灵感数量: {{ (combo.inspirations || combo.inspiration_ids)?.length || 0 }}
          </div>
        </div>
      </div>
      
      <div class="mt-6 flex justify-end">
        <button 
          @click="handleSelectCombination"
          :disabled="!selectedCombinationId || loading"
          class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="loading" class="flex items-center">
            <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            生成中...
          </span>
          <span v-else>生成拓扑图</span>
        </button>
      </div>
    </div>
    
    <div v-if="step === 'topologies'" class="space-y-6">
      <h2 class="text-lg font-semibold">选择拓扑图变体</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div 
          v-for="(topology, index) in topologies" 
          :key="topology.id"
          @click="handleSelectTopology(index)"
          class="bg-white rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
        >
          <div class="p-4">
            <div class="flex items-center space-x-2 mb-3">
              <span class="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold">
                {{ index + 1 }}
              </span>
              <h3 class="text-lg font-semibold text-gray-800">{{ topology.name }}</h3>
            </div>
            <p class="text-sm text-gray-600 mb-4">{{ topology.description }}</p>
            
            <div class="h-64 border border-gray-200 rounded-lg bg-gray-50 overflow-hidden">
              <TopologyGraph 
                :nodes="topology.nodes" 
                :edges="topology.edges"
                :custom-relation-types="customRelationTypes"
                :height="256"
              />
            </div>
            
            <div class="mt-4 text-xs text-gray-500">
              节点: {{ topology.nodes.length }} | 关系: {{ topology.edges.length }}
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="step === 'edit'" class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-lg font-semibold">编辑拓扑图</h2>
          <p class="text-sm text-gray-500">{{ topologies[selectedTopologyIndex]?.name }}</p>
        </div>
        <div class="flex space-x-3">
          <button 
            @click="step = 'topologies'"
            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            返回选择
          </button>
          <button 
            @click="handleGenerateCreatives"
            :disabled="loading"
            class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="loading" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              生成中...
            </span>
            <span v-else>生成创意</span>
          </button>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="border border-gray-200 rounded-lg bg-gray-50 overflow-hidden">
          <TopologyGraph 
            :nodes="currentNodes" 
            :edges="currentEdges"
            :custom-relation-types="customRelationTypes"
            :editable="true"
            :height="400"
            @create-relation="handleCreateRelation"
            @select-edge="handleSelectEdge"
          />
        </div>
        
        <div class="mt-4 flex items-center justify-between">
          <div class="flex items-center space-x-4 text-sm text-gray-500">
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
          
          <div class="text-sm text-gray-500">
            点击节点创建关系，点击连线编辑描述
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="step === 'generating'" class="text-center py-12 bg-white rounded-lg shadow-md">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 mb-4">
        <svg class="animate-spin h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      <h2 class="text-xl font-semibold text-gray-800 mb-2">正在生成创意方案...</h2>
      <p class="text-gray-500">AI正在基于您编辑的拓扑图生成创意</p>
    </div>
    
    <div v-if="step === 'results'" class="space-y-6">
      <div class="flex justify-between items-center">
        <div>
          <h2 class="text-lg font-semibold">生成的创意方案</h2>
          <p class="text-sm text-gray-500">基于 {{ topologies[selectedTopologyIndex]?.name }} 生成</p>
        </div>
        <button 
          @click="step = 'edit'"
          class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
        >
          返回编辑
        </button>
      </div>
      
      <div v-if="generatedCreatives.length === 0" class="text-center py-12 bg-white rounded-lg shadow-md">
        <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 012 2v6a2 2 012 2m-4 2a2 2 011.586 7.707 9.293a1 1 0 001.414 1.414L9 10.586 7.707 9.293z" />
        </svg>
        <p class="text-gray-500 mt-4">没有生成创意</p>
        <button @click="handleGenerateCreatives" class="btn-primary mt-4">
          重新生成
        </button>
      </div>
      
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div 
          v-for="(creative, index) in generatedCreatives" 
          :key="creative.id"
          @click="handleViewCreative(creative)"
          class="bg-white rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
        >
          <div class="p-4">
            <div class="flex items-center space-x-2 mb-3">
              <span class="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-bold">
                {{ index + 1 }}
              </span>
              <h3 class="text-lg font-semibold text-gray-800">{{ creative.title }}</h3>
            </div>
            <p class="text-sm text-gray-600 line-clamp-3 mb-3">{{ creative.description }}</p>
            
            <div v-if="creative.key_points && creative.key_points.length > 0" class="mb-3">
              <h4 class="text-sm font-medium text-gray-700 mb-2">关键点</h4>
              <ul class="text-sm text-gray-600 space-y-1">
                <li v-for="point in creative.key_points.slice(0, 3)" :key="point" class="flex items-start">
                  <span class="text-primary-500 mr-1">•</span>
                  <span>{{ point }}</span>
                </li>
                <li v-if="creative.key_points.length > 3" class="text-xs text-gray-400">
                  +{{ creative.key_points.length - 3 }} 个更多关键点
                </li>
              </ul>
            </div>
            
            <div class="px-4 py-3 bg-gray-50 border-t">
              <span class="text-xs text-gray-400">
                {{ new Date(creative.created_at).toLocaleString() }}
              </span>
            </div>
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
              <option v-for="rt in customRelationTypes.filter(r => r.name !== 'primary' && r.name !== 'parallel' && r.name !== 'contrast')" :key="rt.id" :value="rt.id">
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
    
    <div v-if="selectedCreative" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="selectedCreative = null">
      <div class="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-start mb-4">
            <h2 class="text-xl font-bold">{{ selectedCreative.title }}</h2>
            <button @click="selectedCreative = null" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p class="text-gray-600 mb-6">{{ selectedCreative.description }}</p>
          
          <div v-if="selectedCreative.key_points && selectedCreative.key_points.length > 0" class="mb-6">
            <h3 class="font-semibold mb-2">关键点</h3>
            <ul class="list-disc list-inside space-y-1 text-gray-600">
              <li v-for="point in selectedCreative.key_points" :key="point">{{ point }}</li>
            </ul>
          </div>
          
          <div v-if="selectedCreative.prompt" class="mb-6 p-4 bg-gray-50 rounded-lg">
            <h3 class="font-semibold mb-2">生成的提示词</h3>
            <pre class="text-sm text-gray-700 whitespace-pre-wrap">{{ selectedCreative.prompt }}</pre>
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
              :disabled="generatingPrompt"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              <span v-if="generatingPrompt" class="flex items-center">
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

          <div class="text-sm text-gray-500">
            创建时间: {{ new Date(selectedCreative.created_at).toLocaleString('zh-CN') }}
          </div>
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
              class="input-field" 
              placeholder="例如: D:\projects\creative_output"
            />
          </div>
          <p class="text-xs text-gray-500">
            将把该创意相关的所有源文件复制到指定文件夹中，按文件类型分类存放。
          </p>
          <div class="flex justify-end space-x-3">
            <button @click="showAggregateModal = false" class="btn-secondary">取消</button>
            <button 
              @click="handleAggregateFiles" 
              :disabled="!aggregateOutputFolder || aggregatingFiles"
              class="btn-primary disabled:opacity-50"
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
  </div>
</template>
