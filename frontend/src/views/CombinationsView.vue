<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCombinationStore } from '@/stores/combination'
import { useInspirationStore } from '@/stores/inspiration'
import type { InspirationCombination } from '@/types'

const router = useRouter()
const combinationStore = useCombinationStore()
const inspirationStore = useInspirationStore()

const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingCombination = ref<InspirationCombination | null>(null)

const newCombination = ref({
  name: '',
  description: '',
  inspiration_ids: [] as string[],
  sub_combination_ids: [] as string[]
})

const expandedCombinations = ref<Set<string>>(new Set())

const selectedIds = ref<string[]>([])
const showDeleteConfirm = ref(false)
const deleteTargetId = ref<string | null>(null)
const showBatchDeleteConfirm = ref(false)

onMounted(async () => {
  await Promise.all([
    combinationStore.fetchCombinations(),
    inspirationStore.fetchInspirations()
  ])
})

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
  if (selectedIds.value.length === combinationStore.combinations.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = combinationStore.combinations.map(c => c.id)
  }
}

const toggleInspiration = (id: string) => {
  const index = newCombination.value.inspiration_ids.indexOf(id)
  if (index > -1) {
    newCombination.value.inspiration_ids.splice(index, 1)
  } else {
    newCombination.value.inspiration_ids.push(id)
  }
}

const toggleSubCombination = (id: string) => {
  const index = newCombination.value.sub_combination_ids.indexOf(id)
  if (index > -1) {
    newCombination.value.sub_combination_ids.splice(index, 1)
  } else {
    newCombination.value.sub_combination_ids.push(id)
  }
}

const handleCreateCombination = async () => {
  if (!newCombination.value.name) return
  
  try {
    await combinationStore.createCombination(newCombination.value)
    showCreateModal.value = false
    newCombination.value = {
      name: '',
      description: '',
      inspiration_ids: [],
      sub_combination_ids: []
    }
  } catch (error) {
    console.error('Failed to create combination:', error)
    alert('创建组合失败')
  }
}

const handleEditCombination = (combination: InspirationCombination) => {
  editingCombination.value = { ...combination }
  showEditModal.value = true
}

const handleUpdateCombination = async () => {
  if (!editingCombination.value) return
  
  try {
    await combinationStore.updateCombination(editingCombination.value.id, {
      name: editingCombination.value.name,
      description: editingCombination.value.description,
      inspiration_ids: editingCombination.value.inspirations,
      sub_combination_ids: editingCombination.value.sub_combinations
    })
    showEditModal.value = false
    editingCombination.value = null
  } catch (error) {
    console.error('Failed to update combination:', error)
    alert('更新组合失败')
  }
}

const confirmDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleDeleteCombination = async () => {
  if (!deleteTargetId.value) return
  showDeleteConfirm.value = false
  
  try {
    await combinationStore.deleteCombination(deleteTargetId.value)
    selectedIds.value = selectedIds.value.filter(id => id !== deleteTargetId.value)
  } catch (error) {
    console.error('Failed to delete combination:', error)
    alert('删除组合失败')
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
      await combinationStore.deleteCombination(id)
    } catch (error) {
      console.error('Failed to delete combination:', error)
    }
  }
}

const handleGenerateCreatives = (combination: InspirationCombination) => {
  combinationStore.setCurrentCombination(combination)
  router.push(`/creatives?combination=${combination.id}`)
}

const toggleExpand = (id: string) => {
  if (expandedCombinations.value.has(id)) {
    expandedCombinations.value.delete(id)
  } else {
    expandedCombinations.value.add(id)
  }
}

const getInspirationNames = (ids: string[]): string[] => {
  return ids.map(id => {
    const insp = inspirationStore.getInspiration(id)
    return insp?.name || id
  })
}

const getCombinationName = (id: string): string => {
  const comb = combinationStore.combinations.find(c => c.id === id)
  return comb?.name || id
}

const availableSubCombinations = computed(() => {
  if (!editingCombination.value) return combinationStore.combinations
  return combinationStore.combinations.filter(c => c.id !== editingCombination.value?.id)
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">组合管理</h1>
        <p class="text-gray-500 mt-1">创建灵感组合，支持嵌套组合</p>
      </div>
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
          {{ selectedIds.length === combinationStore.combinations.length ? '取消全选' : '全选' }}
        </button>
        <button @click="showCreateModal = true" class="btn-primary">
          <span class="flex items-center">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            创建组合
          </span>
        </button>
      </div>
    </div>
    
    <div v-if="combinationStore.combinations.length === 0" class="text-center py-12 bg-white rounded-lg shadow-md">
      <svg class="w-16 h-16 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
      <p class="text-gray-500 mt-4">还没有创建任何组合</p>
      <p class="text-gray-400 text-sm mt-1">点击上方按钮创建第一个组合</p>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="combination in combinationStore.combinations" 
        :key="combination.id"
        :class="[
          'bg-white rounded-lg shadow-md overflow-hidden border-2 transition-all cursor-pointer',
          isSelected(combination.id) ? 'border-blue-500' : 'border-transparent'
        ]"
        @click="toggleSelection(combination.id)"
      >
        <div class="p-4">
          <div class="flex justify-between items-start">
            <div class="flex items-start space-x-3">
              <div 
                :class="[
                  'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-1',
                  isSelected(combination.id) ? 'bg-blue-500 border-blue-500' : 'border-gray-300'
                ]"
              >
                <svg v-if="isSelected(combination.id)" class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </div>
              <div class="flex-1">
                <h3 class="font-semibold text-gray-800">{{ combination.name }}</h3>
                <p v-if="combination.description" class="text-sm text-gray-500 mt-1">{{ combination.description }}</p>
              </div>
            </div>
            <div class="flex space-x-1" @click.stop>
              <button @click="handleEditCombination(combination)" class="p-1 text-gray-400 hover:text-primary-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button @click="confirmDelete(combination.id)" class="p-1 text-gray-400 hover:text-red-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
          
          <div class="mt-3 space-y-2 ml-8">
            <div v-if="combination.inspirations.length > 0">
              <div class="flex items-center text-sm text-gray-500">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>{{ combination.inspirations.length }} 个灵感</span>
              </div>
              <div class="flex flex-wrap gap-1 mt-1">
                <span 
                  v-for="name in getInspirationNames(combination.inspirations).slice(0, 3)" 
                  :key="name"
                  class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs"
                >
                  {{ name }}
                </span>
                <span 
                  v-if="combination.inspirations.length > 3"
                  class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  +{{ combination.inspirations.length - 3 }}
                </span>
              </div>
            </div>
            
            <div v-if="combination.sub_combinations.length > 0">
              <div class="flex items-center text-sm text-gray-500">
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
                <span>{{ combination.sub_combinations.length }} 个子组合</span>
              </div>
              <div class="flex flex-wrap gap-1 mt-1">
                <span 
                  v-for="subId in combination.sub_combinations.slice(0, 2)" 
                  :key="subId"
                  class="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs"
                >
                  {{ getCombinationName(subId) }}
                </span>
                <span 
                  v-if="combination.sub_combinations.length > 2"
                  class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  +{{ combination.sub_combinations.length - 2 }}
                </span>
              </div>
            </div>
            
            <div v-if="combination.relations.length > 0" class="flex items-center text-sm text-gray-500">
              <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <span>{{ combination.relations.length }} 个关系</span>
            </div>
          </div>
        </div>
        
        <div class="border-t px-4 py-3 bg-gray-50 flex justify-between items-center" @click.stop>
          <span class="text-xs text-gray-400">
            {{ new Date(combination.created_at).toLocaleDateString() }}
          </span>
          <button 
            @click="handleGenerateCreatives(combination)"
            class="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            生成创意 →
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">创建组合</h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">组合名称 *</label>
            <input v-model="newCombination.name" type="text" class="input-field" placeholder="给组合起个名字" />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <input v-model="newCombination.description" type="text" class="input-field" placeholder="描述这个组合的用途" />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">选择灵感</label>
            <div class="max-h-40 overflow-y-auto border rounded-lg p-2 space-y-1">
              <div 
                v-for="insp in inspirationStore.inspirations" 
                :key="insp.id"
                @click="toggleInspiration(insp.id)"
                :class="[
                  'p-2 rounded cursor-pointer transition-colors',
                  newCombination.inspiration_ids.includes(insp.id)
                    ? 'bg-primary-100 border border-primary-300'
                    : 'hover:bg-gray-100'
                ]"
              >
                <div class="flex justify-between items-center">
                  <span class="text-sm">{{ insp.name }}</span>
                  <span class="text-xs text-gray-400">{{ insp.type }}</span>
                </div>
              </div>
              <div v-if="inspirationStore.inspirations.length === 0" class="text-center text-gray-400 py-4">
                还没有灵感，请先添加灵感
              </div>
            </div>
            <p class="text-xs text-gray-500 mt-1">已选择 {{ newCombination.inspiration_ids.length }} 个灵感</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">选择子组合（可选）</label>
            <div class="max-h-40 overflow-y-auto border rounded-lg p-2 space-y-1">
              <div 
                v-for="comb in combinationStore.combinations" 
                :key="comb.id"
                @click="toggleSubCombination(comb.id)"
                :class="[
                  'p-2 rounded cursor-pointer transition-colors',
                  newCombination.sub_combination_ids.includes(comb.id)
                    ? 'bg-purple-100 border border-purple-300'
                    : 'hover:bg-gray-100'
                ]"
              >
                <div class="flex justify-between items-center">
                  <span class="text-sm">{{ comb.name }}</span>
                  <span class="text-xs text-gray-400">{{ comb.inspirations.length }} 灵感</span>
                </div>
              </div>
              <div v-if="combinationStore.combinations.length === 0" class="text-center text-gray-400 py-4">
                还没有其他组合
              </div>
            </div>
            <p class="text-xs text-gray-500 mt-1">已选择 {{ newCombination.sub_combination_ids.length }} 个子组合</p>
          </div>
        </div>
        
        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showCreateModal = false" class="btn-secondary">取消</button>
          <button @click="handleCreateCombination" class="btn-primary" :disabled="!newCombination.name">创建</button>
        </div>
      </div>
    </div>
    
    <div v-if="showEditModal && editingCombination" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-[600px] max-h-[80vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">编辑组合</h3>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">组合名称 *</label>
            <input v-model="editingCombination.name" type="text" class="input-field" />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <input v-model="editingCombination.description" type="text" class="input-field" />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">选择灵感</label>
            <div class="max-h-40 overflow-y-auto border rounded-lg p-2 space-y-1">
              <div 
                v-for="insp in inspirationStore.inspirations" 
                :key="insp.id"
                @click="() => {
                  const index = editingCombination!.inspirations.indexOf(insp.id)
                  if (index > -1) {
                    editingCombination!.inspirations.splice(index, 1)
                  } else {
                    editingCombination!.inspirations.push(insp.id)
                  }
                }"
                :class="[
                  'p-2 rounded cursor-pointer transition-colors',
                  editingCombination.inspirations.includes(insp.id)
                    ? 'bg-primary-100 border border-primary-300'
                    : 'hover:bg-gray-100'
                ]"
              >
                <div class="flex justify-between items-center">
                  <span class="text-sm">{{ insp.name }}</span>
                  <span class="text-xs text-gray-400">{{ insp.type }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">选择子组合</label>
            <div class="max-h-40 overflow-y-auto border rounded-lg p-2 space-y-1">
              <div 
                v-for="comb in availableSubCombinations" 
                :key="comb.id"
                @click="() => {
                  const index = editingCombination!.sub_combinations.indexOf(comb.id)
                  if (index > -1) {
                    editingCombination!.sub_combinations.splice(index, 1)
                  } else {
                    editingCombination!.sub_combinations.push(comb.id)
                  }
                }"
                :class="[
                  'p-2 rounded cursor-pointer transition-colors',
                  editingCombination.sub_combinations.includes(comb.id)
                    ? 'bg-purple-100 border border-purple-300'
                    : 'hover:bg-gray-100'
                ]"
              >
                <div class="flex justify-between items-center">
                  <span class="text-sm">{{ comb.name }}</span>
                  <span class="text-xs text-gray-400">{{ comb.inspirations.length }} 灵感</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showEditModal = false" class="btn-secondary">取消</button>
          <button @click="handleUpdateCombination" class="btn-primary">保存</button>
        </div>
      </div>
    </div>
    
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">确认删除</h3>
        <p class="text-gray-600 mb-6">确定要删除这个组合吗？此操作不可撤销。</p>
        <div class="flex justify-end space-x-3">
          <button @click="showDeleteConfirm = false; deleteTargetId = null" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">取消</button>
          <button @click="handleDeleteCombination" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">删除</button>
        </div>
      </div>
    </div>
    
    <div v-if="showBatchDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">确认批量删除</h3>
        <p class="text-gray-600 mb-6">确定要删除选中的 {{ selectedIds.length }} 个组合吗？此操作不可撤销。</p>
        <div class="flex justify-end space-x-3">
          <button @click="showBatchDeleteConfirm = false" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">取消</button>
          <button @click="handleBatchDelete" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>
