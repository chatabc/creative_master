<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useInspirationStore } from '@/stores/inspiration'
import { useFileTypeStore } from '@/stores/fileType'
import FileDropZone from '@/components/FileDropZone.vue'
import TreeNode from '@/components/TreeNode.vue'
import type { Inspiration } from '@/types'

const inspirationStore = useInspirationStore()
const fileTypeStore = useFileTypeStore()

onMounted(async () => {
  await Promise.all([
    inspirationStore.fetchInspirations(),
    fileTypeStore.fetchFileTypes()
  ])
})

const isAdding = ref(false)
const addMode = ref<'file' | 'folder'>('file')
const newInspiration = ref({
  sourcePath: '',
  name: '',
  tags: '',
  copyFile: true
})

const selectedType = ref<string>('')
const searchQuery = ref('')
const fileDropZone = ref<InstanceType<typeof FileDropZone> | null>(null)
const folderDropZone = ref<InstanceType<typeof FileDropZone> | null>(null)
const uploadingFiles = ref<any[]>([])
const isUploading = ref(false)

const selectedInspiration = ref<Inspiration | null>(null)
const showDetailModal = ref(false)
const summarizingIds = ref<Set<string>>(new Set())
const summarizeStatus = ref<Map<string, { status: 'loading' | 'success' | 'error', message: string }>>(new Map())

const selectedIds = ref<string[]>([])
const showDeleteConfirm = ref(false)
const deleteTargetId = ref<string | null>(null)
const showBatchDeleteConfirm = ref(false)

const showEditModal = ref(false)
const editingInspiration = ref<Inspiration | null>(null)
const editForm = ref({ 
  name: '', 
  tags: '', 
  summary: '', 
  ignoredPaths: [] as string[],
  // Structured folder summary fields
  folderTree: '',
  folderOverview: '',
  folderImportant: '',
  folderSecondary: '',
  isStructured: false
})
const folderTree = ref<any[]>([])
const fileSummaries = ref<{ path: string; name: string; summary: string }[]>([])
const regeneratingSummaries = ref(false)
const regeneratingSingle = ref<string | null>(null)
const regeneratingSections = ref<Record<string, boolean>>({})
const batchSummarizing = ref(false)

const typeFilters = computed(() => [
  { value: '', label: '全部' },
  ...fileTypeStore.fileTypes.map(ft => ({ value: ft.name, label: ft.display_name }))
])

const parsedSummary = computed(() => {
  if (!selectedInspiration.value || !selectedInspiration.value.summary) return null
  if (selectedInspiration.value.type !== 'folder') return null
  
  try {
    const parsed = JSON.parse(selectedInspiration.value.summary)
    if (parsed.tree && parsed.overview) {
      return parsed
    }
  } catch (e) {
    return null
  }
  return null
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
  const filtered = inspirationStore.filteredInspirations(selectedType.value, searchQuery.value)
  if (selectedIds.value.length === filtered.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = filtered.map((i: Inspiration) => i.id)
  }
}

const handleFilesSelected = (files: (File | FileList)[]) => {
  uploadingFiles.value = files
}

const handleUpload = async () => {
  if (uploadingFiles.value.length === 0) return
  
  isUploading.value = true
  try {
    const tags = newInspiration.value.tags 
      ? newInspiration.value.tags.split(',').map(t => t.trim()).filter(Boolean)
      : []
    
    await inspirationStore.uploadFiles(uploadingFiles.value, tags)
    
    if (addMode.value === 'file') {
      fileDropZone.value?.clearFiles()
    } else {
      folderDropZone.value?.clearFiles()
    }
    uploadingFiles.value = []
    newInspiration.value = { sourcePath: '', name: '', tags: '', copyFile: true }
    isAdding.value = false
  } catch (error) {
    console.error('Upload failed:', error)
    alert('上传失败，请重试')
  } finally {
    isUploading.value = false
  }
}

const openDetail = (inspiration: Inspiration) => {
  selectedInspiration.value = inspiration
  showDetailModal.value = true
}

const closeDetail = () => {
  showDetailModal.value = false
  selectedInspiration.value = null
}

const openEditModal = async (inspiration: Inspiration) => {
  editingInspiration.value = inspiration
  
  let isStructured = false
  let summaryTree = ''
  let summaryOverview = ''
  let summaryImportant = ''
  let summarySecondary = ''
  let summary = inspiration.summary || ''

  if (inspiration.type === 'folder' && summary) {
    try {
      const parsed = JSON.parse(summary)
      if (parsed.tree && parsed.overview) {
        isStructured = true
        summaryTree = parsed.tree
        summaryOverview = parsed.overview
        summaryImportant = parsed.important_docs || ''
        summarySecondary = parsed.secondary_docs || ''
      }
    } catch (e) {
      // Not structured JSON, keep as plain summary
    }
  }

  editForm.value = {
    name: inspiration.name,
    tags: inspiration.tags.join(', '),
    summary: summary,
    ignoredPaths: (inspiration.metadata?.ignored_paths as string[]) || [],
    folderTree: summaryTree,
    folderOverview: summaryOverview,
    folderImportant: summaryImportant,
    folderSecondary: summarySecondary,
    isStructured
  }
  showEditModal.value = true
  
  if (inspiration.type === 'folder') {
    folderTree.value = []
    fileSummaries.value = []
    try {
      const tree = await inspirationStore.getFolderTree(inspiration.id)
      folderTree.value = tree
      
      const summaries = inspiration.metadata?.file_summaries || []
      fileSummaries.value = summaries
    } catch (error) {
      console.error('Failed to load folder tree:', error)
    }
  }
}

const isIgnored = (path: string): boolean => {
  return editForm.value.ignoredPaths.some(ignored => 
    path === ignored || path.startsWith(ignored + '/')
  )
}

const regenerateAllSummaries = async () => {
  if (!editingInspiration.value) return
  
  regeneratingSummaries.value = true
  
  try {
    const response = await inspirationStore.regenerateFolderSummaries(editingInspiration.value.id)
    
    if (response.file_summaries) {
      fileSummaries.value = response.file_summaries
      
      if (editForm.value.summary) {
        editForm.value.summary = response.overall_summary || ''
      }
    }
    
    alert(`已重新生成 ${response.file_summaries.length} 个文件总结`)
  } catch (error) {
    console.error('Failed to regenerate summaries:', error)
    alert('重新生成失败，请重试')
  } finally {
    regeneratingSummaries.value = false
  }
}

const regenerateSingleSummary = async (filePath: string) => {
  if (!editingInspiration.value) return
  
  regeneratingSingle.value = filePath
  
  try {
    const response = await inspirationStore.regenerateSingleSummary(editingInspiration.value.id, filePath)
    
    const index = fileSummaries.value.findIndex(fs => fs.path === filePath)
    if (index > -1 && response.summary) {
      fileSummaries.value[index].summary = response.summary
    }
    
    alert('文件总结已更新')
  } catch (error) {
    console.error('Failed to regenerate single summary:', error)
    alert('重新生成失败，请重试')
  } finally {
    regeneratingSingle.value = null
  }
}

const regenerateSection = async (section: string) => {
  if (!editingInspiration.value) return
  
  regeneratingSections.value[section] = true
  
  try {
    const response = await inspirationStore.regenerateSection(editingInspiration.value.id, section)
    
    // Update the corresponding field in editForm
    if (section === 'tree') editForm.value.folderTree = response
    else if (section === 'overview') editForm.value.folderOverview = response
    // else if (section === 'important_docs') editForm.value.folderImportant = response
    // else if (section === 'secondary_docs') editForm.value.folderSecondary = response
    
    // Also update the summary JSON in editForm so it stays in sync
    try {
      const parsed = JSON.parse(editForm.value.summary || '{}')
      parsed[section] = response
      editForm.value.summary = JSON.stringify(parsed, null, 2)
    } catch (e) {
      // ignore
    }

    alert('部分总结已更新')
  } catch (error) {
    console.error(`Failed to regenerate section ${section}:`, error)
    alert('重新生成失败，请重试')
  } finally {
    regeneratingSections.value[section] = false
  }
}

const toggleIgnorePath = (path: string) => {
  const index = editForm.value.ignoredPaths.indexOf(path)
  if (index > -1) {
    editForm.value.ignoredPaths.splice(index, 1)
  } else {
    editForm.value.ignoredPaths.push(path)
  }
}

const handleEditSave = async () => {
  if (!editingInspiration.value) return
  
  try {
    const tags = editForm.value.tags 
      ? editForm.value.tags.split(',').map(t => t.trim()).filter(Boolean)
      : []
    
    let summary = editForm.value.summary
    
    if (editForm.value.isStructured) {
      try {
        const parsed = JSON.parse(summary || '{}')
        parsed.tree = editForm.value.folderTree
        parsed.overview = editForm.value.folderOverview
        // parsed.important_docs = editForm.value.folderImportant
        // parsed.secondary_docs = editForm.value.folderSecondary
        summary = JSON.stringify(parsed, null, 2)
      } catch (e) {
        // Fallback if parsing fails, though it shouldn't if it was structured
        const newStruct = {
          tree: editForm.value.folderTree,
          overview: editForm.value.folderOverview,
          // important_docs: editForm.value.folderImportant,
          // secondary_docs: editForm.value.folderSecondary
        }
        summary = JSON.stringify(newStruct, null, 2)
      }
    }
    
    await inspirationStore.updateInspiration(editingInspiration.value.id, {
      name: editForm.value.name,
      tags,
      summary: summary,
      metadata: {
        ...editingInspiration.value.metadata,
        ignored_paths: editForm.value.ignoredPaths
      }
    })
    
    showEditModal.value = false
    editingInspiration.value = null
  } catch (error) {
    console.error('Edit failed:', error)
    alert('编辑失败，请重试')
  }
}

const handleSummarize = async (id: string) => {
  summarizingIds.value.add(id)
  summarizeStatus.value.set(id, { status: 'loading', message: '正在生成总结...' })
  
  try {
    await inspirationStore.summarizeInspiration(id)
    summarizeStatus.value.set(id, { status: 'success', message: '总结生成成功！' })
    
    setTimeout(() => {
      summarizeStatus.value.delete(id)
    }, 3000)
  } catch (error) {
    console.error('Summarize failed:', error)
    summarizeStatus.value.set(id, { status: 'error', message: '总结生成失败，请检查AI模型配置' })
    
    setTimeout(() => {
      summarizeStatus.value.delete(id)
    }, 5000)
  } finally {
    summarizingIds.value.delete(id)
  }
}

const confirmDelete = (id: string) => {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

const handleDelete = async () => {
  if (!deleteTargetId.value) return
  showDeleteConfirm.value = false
  
  await inspirationStore.deleteInspiration(deleteTargetId.value)
  if (selectedInspiration.value?.id === deleteTargetId.value) {
    closeDetail()
  }
  selectedIds.value = selectedIds.value.filter(id => id !== deleteTargetId.value)
  deleteTargetId.value = null
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
      await inspirationStore.deleteInspiration(id)
    } catch (error) {
      console.error('Failed to delete inspiration:', error)
    }
  }
}

const handleBatchSummarize = async (regenerate: boolean) => {
  if (selectedIds.value.length === 0) return
  
  batchSummarizing.value = true
  
  const idsToSummarize = selectedIds.value.filter(id => {
    const inspiration = inspirationStore.inspirations.find(i => i.id === id)
    return regenerate || !inspiration?.summary
  })
  
  let successCount = 0
  let skipCount = selectedIds.value.length - idsToSummarize.length
  
  for (const id of idsToSummarize) {
    try {
      summarizingIds.value.add(id)
      summarizeStatus.value.set(id, { status: 'loading', message: '正在生成总结...' })
      await inspirationStore.summarizeInspiration(id)
      summarizeStatus.value.set(id, { status: 'success', message: '总结生成成功！' })
      successCount++
    } catch (error) {
      summarizeStatus.value.set(id, { status: 'error', message: '总结生成失败' })
    }
  }
  
  batchSummarizing.value = false
  
  if (skipCount > 0) {
    alert(`已完成！成功: ${successCount}, 跳过(已有总结): ${skipCount}`)
  } else {
    alert(`已完成！成功: ${successCount}`)
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getTypeColor = (type: string) => fileTypeStore.getTypeColor(type)
const getTypeDisplayName = (type: string) => fileTypeStore.getTypeDisplayName(type)
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">灵感库</h1>
      <div class="flex gap-2">
        <button 
          v-if="selectedIds.length > 0"
          @click="handleBatchSummarize(false)"
          :disabled="batchSummarizing"
          class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
        >
          {{ batchSummarizing ? '生成中...' : '批量生成总结' }} ({{ selectedIds.length }})
        </button>
        <button 
          v-if="selectedIds.length > 0"
          @click="handleBatchSummarize(true)"
          :disabled="batchSummarizing"
          class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
        >
          {{ batchSummarizing ? '生成中...' : '批量重新生成总结' }} ({{ selectedIds.length }})
        </button>
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
          {{ selectedIds.length === inspirationStore.filteredInspirations(selectedType, searchQuery).length ? '取消全选' : '全选' }}
        </button>
        <button @click="isAdding = true" class="btn-primary flex items-center space-x-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span>添加灵感</span>
        </button>
      </div>
    </div>
    
    <div class="flex space-x-4">
      <div class="flex-1">
        <input 
          v-model="searchQuery"
          type="text" 
          placeholder="搜索灵感..." 
          class="input-field"
        />
      </div>
      <select v-model="selectedType" class="input-field w-40">
        <option v-for="filter in typeFilters" :key="filter.value" :value="filter.value">
          {{ filter.label }}
        </option>
      </select>
    </div>
    
    <div v-if="isAdding" class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold">添加新灵感</h2>
        <button @click="isAdding = false" class="text-gray-500 hover:text-gray-700">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div class="flex space-x-4 mb-4">
        <button 
          @click="addMode = 'file'"
          :class="['px-4 py-2 rounded-lg font-medium transition-colors', addMode === 'file' ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200']"
        >
          上传文件
        </button>
        <button 
          @click="addMode = 'folder'"
          :class="['px-4 py-2 rounded-lg font-medium transition-colors', addMode === 'folder' ? 'bg-primary-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200']"
        >
          上传文件夹
        </button>
      </div>
      
      <div v-if="addMode === 'file'" class="space-y-4">
        <FileDropZone 
          ref="fileDropZone"
          multiple
          @files-selected="handleFilesSelected"
        />
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">名称（可选，单文件时生效）</label>
          <input v-model="newInspiration.name" type="text" class="input-field" placeholder="自定义名称" />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">标签（逗号分隔）</label>
          <input v-model="newInspiration.tags" type="text" class="input-field" placeholder="设计, UI, 参考" />
        </div>
        
        <div class="flex justify-end space-x-3">
          <button @click="isAdding = false" class="btn-secondary">取消</button>
          <button 
            @click="handleUpload" 
            :disabled="uploadingFiles.length === 0 || isUploading"
            class="btn-primary disabled:opacity-50"
          >
            {{ isUploading ? '上传中...' : '上传' }}
          </button>
        </div>
      </div>
      
      <div v-else class="space-y-4">
        <FileDropZone 
          ref="folderDropZone"
          :multiple="false"
          @files-selected="handleFilesSelected"
        />
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">标签（逗号分隔）</label>
          <input v-model="newInspiration.tags" type="text" class="input-field" placeholder="设计, UI, 参考" />
        </div>
        
        <div class="flex justify-end space-x-3">
          <button @click="isAdding = false" class="btn-secondary">取消</button>
          <button 
            @click="handleUpload" 
            :disabled="uploadingFiles.length === 0 || isUploading"
            class="btn-primary disabled:opacity-50"
          >
            {{ isUploading ? '上传中...' : '上传' }}
          </button>
        </div>
      </div>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="inspiration in inspirationStore.filteredInspirations(selectedType, searchQuery)" 
        :key="inspiration.id"
        :class="[
          'inspiration-card cursor-pointer hover:shadow-lg transition-all border-2',
          isSelected(inspiration.id) ? 'border-blue-500 bg-blue-50' : 'border-transparent'
        ]"
        @click="toggleSelection(inspiration.id)"
      >
        <div class="flex justify-between items-start mb-3">
          <div class="flex items-start space-x-3">
            <div 
              :class="[
                'w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 mt-1',
                isSelected(inspiration.id) ? 'bg-blue-500 border-blue-500' : 'border-gray-300'
              ]"
            >
              <svg v-if="isSelected(inspiration.id)" class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-gray-800">{{ inspiration.name }}</h3>
              <span 
                class="inline-block px-2 py-0.5 rounded-full text-xs font-medium text-white mt-1"
                :style="{ backgroundColor: getTypeColor(inspiration.type) }"
              >
                {{ getTypeDisplayName(inspiration.type) }}
              </span>
            </div>
          </div>
          <div class="flex space-x-2" @click.stop>
            <button 
              @click="openEditModal(inspiration)" 
              class="text-gray-500 hover:text-gray-700"
              title="编辑"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button 
              @click="handleSummarize(inspiration.id)" 
              :disabled="summarizingIds.has(inspiration.id)"
              :class="[
                'transition-colors',
                summarizingIds.has(inspiration.id) 
                  ? 'text-gray-400 cursor-wait' 
                  : 'text-primary-600 hover:text-primary-700'
              ]"
              title="AI总结"
            >
              <svg v-if="summarizingIds.has(inspiration.id)" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </button>
            <button @click="confirmDelete(inspiration.id)" class="text-red-500 hover:text-red-600" title="删除">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        
        <div v-if="summarizeStatus.has(inspiration.id)" class="mb-3">
          <div 
            :class="[
              'px-3 py-2 rounded-lg text-sm flex items-center space-x-2',
              summarizeStatus.get(inspiration.id)?.status === 'loading' ? 'bg-blue-50 text-blue-700' : '',
              summarizeStatus.get(inspiration.id)?.status === 'success' ? 'bg-green-50 text-green-700' : '',
              summarizeStatus.get(inspiration.id)?.status === 'error' ? 'bg-red-50 text-red-700' : ''
            ]"
          >
            <svg v-if="summarizeStatus.get(inspiration.id)?.status === 'loading'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else-if="summarizeStatus.get(inspiration.id)?.status === 'success'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else-if="summarizeStatus.get(inspiration.id)?.status === 'error'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span>{{ summarizeStatus.get(inspiration.id)?.message }}</span>
          </div>
        </div>
        
        <div v-if="inspiration.tags.length > 0" class="flex flex-wrap gap-1 mb-3">
          <span v-for="tag in inspiration.tags" :key="tag" class="tag bg-gray-100 text-gray-600">
            {{ tag }}
          </span>
        </div>
        
        <div v-if="inspiration.summary" class="text-sm text-gray-600 line-clamp-3">
          {{ inspiration.summary }}
        </div>
        
        <div class="mt-3 text-xs text-gray-400">
          {{ new Date(inspiration.created_at).toLocaleDateString() }}
        </div>
      </div>
    </div>
    
    <div v-if="inspirationStore.inspirations.length === 0" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
      <p class="mt-4 text-gray-500">还没有灵感，点击上方按钮添加第一个灵感吧！</p>
    </div>
    
    <div v-if="showDetailModal && selectedInspiration" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="closeDetail">
      <div class="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div class="p-6 border-b border-gray-200">
          <div class="flex justify-between items-start">
            <div>
              <h2 class="text-xl font-bold text-gray-800">{{ selectedInspiration.name }}</h2>
              <div class="flex items-center space-x-3 mt-2">
                <span 
                  class="px-3 py-1 rounded-full text-sm font-medium text-white"
                  :style="{ backgroundColor: getTypeColor(selectedInspiration.type) }"
                >
                  {{ getTypeDisplayName(selectedInspiration.type) }}
                </span>
                <span class="text-sm text-gray-500">
                  {{ new Date(selectedInspiration.created_at).toLocaleString() }}
                </span>
              </div>
            </div>
            <button @click="closeDetail" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <div class="p-6 overflow-y-auto max-h-[60vh] space-y-6">
          <div v-if="selectedInspiration.tags.length > 0">
            <h3 class="text-sm font-medium text-gray-500 mb-2">标签</h3>
            <div class="flex flex-wrap gap-2">
              <span 
                v-for="tag in selectedInspiration.tags" 
                :key="tag" 
                class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
              >
                {{ tag }}
              </span>
            </div>
          </div>
          
          <div>
            <h3 class="text-sm font-medium text-gray-500 mb-2">文件路径</h3>
            <p class="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg break-all font-mono">
              {{ selectedInspiration.path }}
            </p>
          </div>
          
          <div v-if="selectedInspiration.metadata">
            <h3 class="text-sm font-medium text-gray-500 mb-2">文件信息</h3>
            <div class="bg-gray-50 p-3 rounded-lg space-y-1 text-sm">
              <p v-if="selectedInspiration.metadata.size">
                <span class="text-gray-500">大小：</span>
                <span class="text-gray-700">{{ formatFileSize(selectedInspiration.metadata.size) }}</span>
              </p>
              <p v-if="selectedInspiration.metadata.extension">
                <span class="text-gray-500">扩展名：</span>
                <span class="text-gray-700">{{ selectedInspiration.metadata.extension }}</span>
              </p>
              <p v-if="selectedInspiration.metadata.original_path">
                <span class="text-gray-500">原始路径：</span>
                <span class="text-gray-700 break-all">{{ selectedInspiration.metadata.original_path }}</span>
              </p>
            </div>
          </div>
          
          <div>
            <div class="flex justify-between items-center mb-2">
              <h3 class="text-sm font-medium text-gray-500">AI 总结</h3>
              <button 
                @click="handleSummarize(selectedInspiration.id)"
                :disabled="summarizingIds.has(selectedInspiration.id)"
                class="text-sm text-primary-600 hover:text-primary-700 disabled:text-gray-400 flex items-center space-x-1"
              >
                <svg v-if="summarizingIds.has(selectedInspiration.id)" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>{{ summarizingIds.has(selectedInspiration.id) ? '生成中...' : '重新生成' }}</span>
              </button>
            </div>
            
            <div v-if="summarizeStatus.has(selectedInspiration.id)" class="mb-3">
              <div 
                :class="[
                  'px-3 py-2 rounded-lg text-sm flex items-center space-x-2',
                  summarizeStatus.get(selectedInspiration.id)?.status === 'loading' ? 'bg-blue-50 text-blue-700' : '',
                  summarizeStatus.get(selectedInspiration.id)?.status === 'success' ? 'bg-green-50 text-green-700' : '',
                  summarizeStatus.get(selectedInspiration.id)?.status === 'error' ? 'bg-red-50 text-red-700' : ''
                ]"
              >
                <span>{{ summarizeStatus.get(selectedInspiration.id)?.message }}</span>
              </div>
            </div>
            
            <div v-if="parsedSummary" class="bg-gray-50 p-4 rounded-lg space-y-4 text-sm">
              <div>
                <h4 class="font-bold text-gray-800 mb-2">文件夹结构</h4>
                <pre class="text-xs font-mono bg-white p-2 rounded border overflow-x-auto whitespace-pre">{{ parsedSummary.tree }}</pre>
              </div>
              <div>
                <h4 class="font-bold text-gray-800 mb-2">总体说明</h4>
                <p class="text-gray-700 whitespace-pre-wrap">{{ parsedSummary.overview }}</p>
              </div>
            </div>
            <div v-else-if="selectedInspiration.summary" class="bg-gray-50 p-4 rounded-lg">
              <p class="text-gray-700 whitespace-pre-wrap">{{ selectedInspiration.summary }}</p>
            </div>
            <div v-else class="bg-gray-50 p-4 rounded-lg text-center">
              <p class="text-gray-500">暂无总结</p>
              <button 
                @click="handleSummarize(selectedInspiration.id)"
                :disabled="summarizingIds.has(selectedInspiration.id)"
                class="mt-2 text-primary-600 hover:text-primary-700 text-sm"
              >
                点击生成AI总结
              </button>
            </div>
          </div>
          
          <div v-if="selectedInspiration.type === 'folder' && selectedInspiration.metadata?.file_summaries && selectedInspiration.metadata.file_summaries.length > 0">
            <h3 class="text-sm font-medium text-gray-500 mb-2">文件详情</h3>
            <div class="bg-gray-50 p-3 rounded-lg max-h-[400px] overflow-y-auto space-y-3">
              <div 
                v-for="fs in selectedInspiration.metadata.file_summaries" 
                :key="fs.path"
                class="border border-gray-200 rounded-lg p-3 hover:bg-gray-100"
              >
                <div class="flex justify-between items-start mb-2">
                  <div class="flex-1">
                    <div class="text-sm font-medium text-gray-700">{{ fs.name }}</div>
                    <div class="text-xs text-gray-400">{{ fs.path }}</div>
                  </div>
                </div>
                <div class="text-sm text-gray-600 whitespace-pre-wrap">{{ fs.summary }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="p-4 border-t border-gray-200 flex justify-end space-x-3">
          <button @click="closeDetail" class="btn-secondary">关闭</button>
          <button 
            @click="confirmDelete(selectedInspiration.id); closeDetail()" 
            class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            删除
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">确认删除</h3>
        <p class="text-gray-600 mb-6">确定要删除这个灵感吗？此操作不可撤销。</p>
        <div class="flex justify-end space-x-3">
          <button @click="showDeleteConfirm = false; deleteTargetId = null" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">取消</button>
          <button @click="handleDelete" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">删除</button>
        </div>
      </div>
    </div>
    
    <div v-if="showBatchDeleteConfirm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">确认批量删除</h3>
        <p class="text-gray-600 mb-6">确定要删除选中的 {{ selectedIds.length }} 个灵感吗？此操作不可撤销。</p>
        <div class="flex justify-end space-x-3">
          <button @click="showBatchDeleteConfirm = false" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">取消</button>
          <button @click="handleBatchDelete" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">删除</button>
        </div>
      </div>
    </div>
    
    <div v-if="showEditModal && editingInspiration" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-[800px] max-h-[85vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">编辑灵感</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">名称</label>
            <input v-model="editForm.name" type="text" class="input-field" placeholder="灵感名称" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">标签（逗号分隔）</label>
            <input v-model="editForm.tags" type="text" class="input-field" placeholder="设计, UI, 参考" />
          </div>
          
          <div v-if="editingInspiration.type === 'folder'" class="border-t pt-4">
            <div class="flex justify-between items-center mb-2">
              <label class="block text-sm font-medium text-gray-700">忽略的文件/文件夹</label>
              <span class="text-xs text-gray-500">勾选的项在生成AI总结时会被忽略</span>
            </div>
            <div class="bg-gray-50 rounded-lg p-3 max-h-[250px] overflow-y-auto">
              <div v-if="folderTree.length === 0" class="text-gray-500 text-sm text-center py-4">
                加载文件夹结构中...
              </div>
              <TreeNode 
                v-else
                v-for="node in folderTree" 
                :key="node.path"
                :node="node"
                :ignored-paths="editForm.ignoredPaths"
                @toggle-ignore="toggleIgnorePath"
              />
            </div>
          </div>
          
          <div v-if="editingInspiration.type === 'folder'" class="border-t pt-4">
            <div class="flex justify-between items-center mb-2">
              <label class="block text-sm font-medium text-gray-700">文件总结</label>
              <button 
                @click="regenerateAllSummaries" 
                :disabled="regeneratingSummaries"
                class="text-sm text-primary-600 hover:text-primary-700 disabled:opacity-50"
              >
                {{ regeneratingSummaries ? '重新生成中...' : '全部重新生成' }}
              </button>
            </div>
            <div class="bg-gray-50 rounded-lg p-3 max-h-[300px] overflow-y-auto">
              <div v-if="fileSummaries.length === 0" class="text-gray-500 text-sm text-center py-4">
                {{ editForm.summary ? '已有总结，点击"全部重新生成"查看详情' : '请先生成AI总结' }}
              </div>
              <div v-else class="space-y-3">
                <div 
                  v-for="(fs, index) in fileSummaries" 
                  :key="fs.path"
                  class="border border-gray-200 rounded-lg p-3 hover:bg-gray-50"
                >
                  <div class="flex justify-between items-start mb-2">
                    <div class="flex-1">
                      <div class="flex items-center space-x-2">
                        <span 
                          :class="[
                            'text-sm font-medium',
                            isIgnored(fs.path) ? 'text-gray-400 line-through' : 'text-gray-700'
                          ]"
                        >
                          {{ fs.name }}
                        </span>
                        <span v-if="isIgnored(fs.path)" class="text-xs text-yellow-500 ml-2">
                          (已忽略)
                        </span>
                      </div>
                      <span class="text-xs text-gray-400">
                        {{ fs.path }}
                      </span>
                    </div>
                    <button 
                      @click="regenerateSingleSummary(fs.path)"
                      :disabled="regeneratingSingle === fs.path"
                      class="text-xs text-primary-600 hover:text-primary-700 disabled:opacity-50"
                    >
                      {{ regeneratingSingle === fs.path ? '生成中...' : '重新生成' }}
                    </button>
                  </div>
                  <div class="text-sm text-gray-600 whitespace-pre-wrap">{{ fs.summary }}</div>
                </div>
              </div>
            </div>
          </div>
          
          <div v-if="editingInspiration.type !== 'folder' || !editForm.isStructured">
            <label class="block text-sm font-medium text-gray-700 mb-1">AI总结</label>
            <textarea 
              v-model="editForm.summary" 
              class="input-field min-h-[120px] resize-y" 
              placeholder="AI总结内容..."
            ></textarea>
          </div>

          <div v-if="editingInspiration.type === 'folder' && editForm.isStructured" class="space-y-4 border-t pt-4">
             <div>
               <div class="flex justify-between items-center mb-1">
                 <label class="block text-sm font-medium text-gray-700">文件夹结构树</label>
                 <button @click="regenerateSection('tree')" :disabled="regeneratingSections['tree']" class="text-xs text-primary-600 hover:text-primary-700 disabled:opacity-50">
                   {{ regeneratingSections['tree'] ? '生成中...' : '重新生成' }}
                 </button>
               </div>
               <textarea v-model="editForm.folderTree" class="input-field min-h-[150px] font-mono text-xs whitespace-pre" placeholder="文件夹结构..."></textarea>
             </div>
             
             <div>
               <div class="flex justify-between items-center mb-1">
                 <label class="block text-sm font-medium text-gray-700">总体说明</label>
                 <button @click="regenerateSection('overview')" :disabled="regeneratingSections['overview']" class="text-xs text-primary-600 hover:text-primary-700 disabled:opacity-50">
                   {{ regeneratingSections['overview'] ? '生成中...' : '重新生成' }}
                 </button>
               </div>
               <textarea v-model="editForm.folderOverview" class="input-field min-h-[100px]" placeholder="总体说明..."></textarea>
             </div>
          </div>
        </div>
        <div class="flex justify-end space-x-3 mt-6">
          <button @click="showEditModal = false" class="btn-secondary">取消</button>
          <button @click="handleEditSave" class="btn-primary">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>
