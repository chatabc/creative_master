<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useFileTypeStore } from '@/stores/fileType'
import type { CustomFileType, AIModelConfig } from '@/types'

const settingsStore = useSettingsStore()
const fileTypeStore = useFileTypeStore()

onMounted(async () => {
  await Promise.all([
    settingsStore.fetchModelConfigs(),
    fileTypeStore.fetchFileTypes()
  ])
})

const activeTab = ref<'models' | 'fileTypes'>('fileTypes')

const isAddingModel = ref(false)
const editingModel = ref<AIModelConfig | null>(null)
const newModel = ref({
  name: '',
  provider: 'openai',
  model_name: '',
  api_key: '',
  base_url: '',
  file_types: [] as string[],
  is_default: false,
  is_relation_completer: false,
  is_topology_generator: false,
  is_inspiration_generator: false
})

const isAddingFileType = ref(false)
const editingFileType = ref<CustomFileType | null>(null)
const newFileType = ref({
  name: '',
  display_name: '',
  extensions: '',
  icon: '',
  color: '#6b7280',
  description: ''
})

const handleAddModel = async () => {
  if (!newModel.value.name || !newModel.value.api_key) return
  
  let modelName = newModel.value.model_name
  if (!modelName) {
    if (newModel.value.provider === 'openai') modelName = 'gpt-4'
    else if (newModel.value.provider === 'anthropic') modelName = 'claude-3-opus'
    else if (newModel.value.provider === 'google') modelName = 'gemini-pro'
    else modelName = ''
  }
  
  try {
    await settingsStore.addModelConfig({
      name: newModel.value.name,
      provider: newModel.value.provider,
      model_name: modelName,
      api_key: newModel.value.api_key,
      base_url: newModel.value.base_url || undefined,
      file_types: newModel.value.file_types,
      is_default: newModel.value.is_default,
      is_relation_completer: newModel.value.is_relation_completer,
      is_topology_generator: newModel.value.is_topology_generator,
      is_inspiration_generator: newModel.value.is_inspiration_generator
    })
    
    isAddingModel.value = false
    newModel.value = {
      name: '',
      provider: 'openai',
      model_name: '',
      api_key: '',
      base_url: '',
      file_types: [],
      is_default: false,
      is_relation_completer: false,
      is_topology_generator: false,
      is_inspiration_generator: false
    }
  } catch (error) {
    console.error('Failed to add model:', error)
    alert('保存模型配置失败，请检查网络连接')
  }
}

const handleDeleteModel = async (id: string) => {
  if (confirm('确定要删除这个模型配置吗？')) {
    await settingsStore.deleteModelConfig(id)
  }
}

const handleCopyModel = async (model: AIModelConfig) => {
  try {
    await settingsStore.addModelConfig({
      name: `${model.name} (副本)`,
      provider: model.provider,
      model_name: model.model_name,
      api_key: model.api_key,
      base_url: model.base_url || undefined,
      file_types: [...model.file_types],
      is_default: false,
      is_relation_completer: false,
      is_topology_generator: false,
      is_inspiration_generator: false
    })
  } catch (error) {
    console.error('Failed to copy model:', error)
    alert('复制模型配置失败')
  }
}

const handleEditModel = (model: AIModelConfig) => {
  editingModel.value = { ...model }
}

const handleUpdateModel = async () => {
  if (!editingModel.value) return
  
  try {
    await settingsStore.updateModelConfig(editingModel.value.id, {
      name: editingModel.value.name,
      provider: editingModel.value.provider,
      model_name: editingModel.value.model_name,
      api_key: editingModel.value.api_key,
      base_url: editingModel.value.base_url || undefined,
      file_types: editingModel.value.file_types,
      is_default: editingModel.value.is_default,
      is_relation_completer: editingModel.value.is_relation_completer,
      is_topology_generator: editingModel.value.is_topology_generator,
      is_inspiration_generator: editingModel.value.is_inspiration_generator
    })
    editingModel.value = null
  } catch (error) {
    console.error('Failed to update model:', error)
    alert('更新模型配置失败')
  }
}

const toggleFileTypeForEditModel = (typeName: string) => {
  if (!editingModel.value) return
  const index = editingModel.value.file_types.indexOf(typeName)
  if (index > -1) {
    editingModel.value.file_types.splice(index, 1)
  } else {
    editingModel.value.file_types.push(typeName)
  }
}

const toggleFileTypeForModel = (typeName: string) => {
  const index = newModel.value.file_types.indexOf(typeName)
  if (index > -1) {
    newModel.value.file_types.splice(index, 1)
  } else {
    newModel.value.file_types.push(typeName)
  }
}

const handleAddFileType = async () => {
  if (!newFileType.value.name || !newFileType.value.display_name) return
  
  const extensions = newFileType.value.extensions
    .split(',')
    .map(e => e.trim().startsWith('.') ? e.trim() : '.' + e.trim())
    .filter(Boolean)
  
  try {
    const result = await fileTypeStore.addFileType({
      name: newFileType.value.name.toLowerCase().replace(/\s+/g, '_'),
      display_name: newFileType.value.display_name,
      extensions,
      icon: newFileType.value.icon || undefined,
      color: newFileType.value.color,
      description: newFileType.value.description || undefined
    })
    
    if (!result.success && result.conflicts && result.conflicts.length > 0) {
      const conflictMessages = result.conflicts.map(c => 
        `后缀 "${c.extension}" 已存在于 "${c.current_display_name}" 中`
      ).join('\n')
      
      const confirmed = confirm(
        `检测到后缀冲突：\n\n${conflictMessages}\n\n是否将这些后缀从原类型中移除并添加到新类型？`
      )
      
      if (confirmed) {
        const extensionsToReplace = result.conflicts.map(c => c.extension)
        await fileTypeStore.addFileType({
          name: newFileType.value.name.toLowerCase().replace(/\s+/g, '_'),
          display_name: newFileType.value.display_name,
          extensions,
          icon: newFileType.value.icon || undefined,
          color: newFileType.value.color,
          description: newFileType.value.description || undefined,
          force_replace: true,
          extensions_to_replace: extensionsToReplace
        })
      } else {
        return
      }
    }
    
    isAddingFileType.value = false
    newFileType.value = {
      name: '',
      display_name: '',
      extensions: '',
      icon: '',
      color: '#6b7280',
      description: ''
    }
  } catch (error) {
    console.error('Failed to add file type:', error)
    alert('添加文件类型失败，请检查名称是否重复')
  }
}

const handleEditFileType = (fileType: CustomFileType) => {
  editingFileType.value = { ...fileType }
}

const handleUpdateFileType = async () => {
  if (!editingFileType.value) return
  
  try {
    const result = await fileTypeStore.updateFileType(editingFileType.value.id, {
      display_name: editingFileType.value.display_name,
      extensions: editingFileType.value.extensions,
      icon: editingFileType.value.icon,
      color: editingFileType.value.color,
      description: editingFileType.value.description,
      text_mode: editingFileType.value.text_mode
    })
    
    if (!result.success && result.conflicts && result.conflicts.length > 0) {
      const conflictMessages = result.conflicts.map(c => 
        `后缀 "${c.extension}" 已存在于 "${c.current_display_name}" 中`
      ).join('\n')
      
      const confirmed = confirm(
        `检测到后缀冲突：\n\n${conflictMessages}\n\n是否将这些后缀从原类型中移除并添加到此类型？`
      )
      
      if (confirmed) {
        const extensionsToReplace = result.conflicts.map(c => c.extension)
        await fileTypeStore.updateFileType(editingFileType.value.id, {
          display_name: editingFileType.value.display_name,
          extensions: editingFileType.value.extensions,
          icon: editingFileType.value.icon,
          color: editingFileType.value.color,
          description: editingFileType.value.description,
          text_mode: editingFileType.value.text_mode,
          force_replace: true,
          extensions_to_replace: extensionsToReplace
        })
      } else {
        return
      }
    }
    
    editingFileType.value = null
  } catch (error) {
    console.error('Failed to update file type:', error)
    alert('更新文件类型失败')
  }
}

const handleDeleteFileType = async (id: string) => {
  if (confirm('确定要删除这个文件类型吗？')) {
    await fileTypeStore.deleteFileType(id)
  }
}

const handleResetFileTypes = async () => {
  if (confirm('确定要重置所有文件类型到默认设置吗？这将删除所有自定义类型。')) {
    await fileTypeStore.resetToDefault()
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">设置</h1>
    </div>
    
    <div class="flex space-x-4 border-b border-gray-200 mb-6">
      <button 
        @click="activeTab = 'fileTypes'"
        :class="['px-4 py-2 font-medium transition-colors border-b-2', activeTab === 'fileTypes' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
      >
        文件类型管理
      </button>
      <button 
        @click="activeTab = 'models'"
        :class="['px-4 py-2 font-medium transition-colors border-b-2', activeTab === 'models' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700']"
      >
        AI 模型配置
      </button>
    </div>
    
    <!-- File Types Tab -->
    <div v-if="activeTab === 'fileTypes'" class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-semibold">文件类型管理</h2>
        <div class="flex space-x-3">
          <button @click="handleResetFileTypes" class="btn-secondary">
            重置默认
          </button>
          <button @click="isAddingFileType = true" class="btn-primary">
            添加类型
          </button>
        </div>
      </div>
      
      <div v-if="isAddingFileType" class="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 class="text-md font-medium mb-4">添加新文件类型</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">类型名称（英文）</label>
            <input v-model="newFileType.name" type="text" class="input-field" placeholder="如：model" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">显示名称（中文）</label>
            <input v-model="newFileType.display_name" type="text" class="input-field" placeholder="如：模型文件" />
          </div>
          <div class="col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">文件后缀（逗号分隔）</label>
            <input v-model="newFileType.extensions" type="text" class="input-field" placeholder="如：.pt, .pth, .onnx" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">颜色</label>
            <div class="flex items-center space-x-2">
              <input v-model="newFileType.color" type="color" class="w-10 h-10 rounded cursor-pointer" />
              <input v-model="newFileType.color" type="text" class="input-field flex-1" placeholder="#6b7280" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
            <input v-model="newFileType.description" type="text" class="input-field" placeholder="文件类型描述" />
          </div>
        </div>
        
        <div class="mt-4 flex justify-end space-x-3">
          <button @click="isAddingFileType = false" class="btn-secondary">取消</button>
          <button @click="handleAddFileType" class="btn-primary">保存</button>
        </div>
      </div>
      
      <div class="space-y-4">
        <div 
          v-for="fileType in fileTypeStore.fileTypes" 
          :key="fileType.id"
          class="border border-gray-200 rounded-lg p-4"
        >
          <div v-if="editingFileType?.id === fileType.id" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">显示名称</label>
                <input v-model="editingFileType.display_name" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">颜色</label>
                <div class="flex items-center space-x-2">
                  <input v-model="editingFileType.color" type="color" class="w-10 h-10 rounded cursor-pointer" />
                  <input v-model="editingFileType.color" type="text" class="input-field flex-1" />
                </div>
              </div>
              <div class="col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">文件后缀（逗号分隔）</label>
                <input 
                  :value="editingFileType.extensions.join(', ')"
                  @input="editingFileType.extensions = ($event.target as HTMLInputElement).value.split(',').map(e => e.trim()).filter(Boolean)"
                  type="text" 
                  class="input-field" 
                />
              </div>
              <div class="col-span-2">
                <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <input v-model="editingFileType.description" type="text" class="input-field" />
              </div>
              <div class="col-span-2">
                <label class="flex items-center space-x-3 cursor-pointer">
                  <input 
                    v-model="editingFileType.text_mode" 
                    type="checkbox" 
                    class="w-5 h-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <div>
                    <span class="text-sm font-medium text-gray-700">文本模式</span>
                    <p class="text-xs text-gray-500">开启后，此类型文件的内容将以纯文本形式发送给AI</p>
                  </div>
                </label>
              </div>
            </div>
            <div class="flex justify-end space-x-3">
              <button @click="editingFileType = null" class="btn-secondary">取消</button>
              <button @click="handleUpdateFileType" class="btn-primary">保存</button>
            </div>
          </div>
          
          <div v-else class="flex justify-between items-start">
            <div class="flex items-start space-x-4">
              <div 
                class="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold"
                :style="{ backgroundColor: fileType.color }"
              >
                {{ fileType.display_name.charAt(0) }}
              </div>
              <div>
                <div class="flex items-center space-x-2">
                  <h3 class="font-semibold text-gray-800">{{ fileType.display_name }}</h3>
                  <span class="text-xs text-gray-400">{{ fileType.name }}</span>
                  <span v-if="fileType.text_mode" class="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">文本模式</span>
                </div>
                <p v-if="fileType.description" class="text-sm text-gray-500 mt-1">{{ fileType.description }}</p>
                <div v-if="fileType.extensions.length > 0" class="flex flex-wrap gap-1 mt-2">
                  <span 
                    v-for="ext in fileType.extensions" 
                    :key="ext"
                    class="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                  >
                    {{ ext }}
                  </span>
                </div>
              </div>
            </div>
            <div class="flex space-x-2">
              <button @click="handleEditFileType(fileType)" class="text-primary-600 hover:text-primary-700">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button 
                v-if="fileType.name !== 'other'"
                @click="handleDeleteFileType(fileType.id)" 
                class="text-red-500 hover:text-red-600"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Models Tab -->
    <div v-if="activeTab === 'models'" class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-semibold">AI 模型配置</h2>
        <button @click="isAddingModel = true" class="btn-primary">
          添加模型
        </button>
      </div>
      
      <div v-if="isAddingModel" class="bg-gray-50 rounded-lg p-6 mb-6">
        <h3 class="text-md font-medium mb-4">添加新模型</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">配置名称</label>
            <input v-model="newModel.name" type="text" class="input-field" placeholder="如：GPT-4 图片分析" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">提供商</label>
            <select v-model="newModel.provider" class="input-field">
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="google">Google</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
            <input v-model="newModel.model_name" type="text" class="input-field" placeholder="如：gpt-4-vision-preview" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
            <input v-model="newModel.api_key" type="password" class="input-field" placeholder="sk-..." />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Base URL（可选）</label>
            <input v-model="newModel.base_url" type="text" class="input-field" placeholder="自定义API地址" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">适用文件类型</label>
            <div class="flex flex-wrap gap-2 mt-2 max-h-32 overflow-y-auto">
              <button 
                v-for="ft in fileTypeStore.fileTypes" 
                :key="ft.id"
                @click="toggleFileTypeForModel(ft.name)"
                :class="[
                  'px-3 py-1 rounded-full text-sm transition-colors',
                  newModel.file_types.includes(ft.name)
                    ? 'text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                ]"
                :style="newModel.file_types.includes(ft.name) ? { backgroundColor: ft.color } : {}"
              >
                {{ ft.display_name }}
              </button>
            </div>
          </div>
        </div>
        
        <div class="mt-4 flex items-center">
          <input v-model="newModel.is_default" type="checkbox" id="isDefault" class="mr-2" />
          <label for="isDefault" class="text-sm text-gray-700">设为默认模型</label>
        </div>
        
        <div class="mt-4 border-t pt-4">
          <p class="text-sm font-medium text-gray-700 mb-3">AI用途配置（每种用途只能选择一个模型）</p>
          <div class="space-y-2">
            <div class="flex items-center">
              <input v-model="newModel.is_relation_completer" type="checkbox" id="isRelationCompleter" class="mr-2" />
              <label for="isRelationCompleter" class="text-sm text-gray-700">作为补全关系图的AI</label>
            </div>
            <div class="flex items-center">
              <input v-model="newModel.is_topology_generator" type="checkbox" id="isTopologyGenerator" class="mr-2" />
              <label for="isTopologyGenerator" class="text-sm text-gray-700">作为生成拓扑图的AI</label>
            </div>
            <div class="flex items-center">
              <input v-model="newModel.is_inspiration_generator" type="checkbox" id="isInspirationGenerator" class="mr-2" />
              <label for="isInspirationGenerator" class="text-sm text-gray-700">作为生成创意的AI</label>
            </div>
          </div>
        </div>
        
        <div class="mt-4 flex justify-end space-x-3">
          <button @click="isAddingModel = false" class="btn-secondary">取消</button>
          <button @click="handleAddModel" class="btn-primary">保存</button>
        </div>
      </div>
      
      <div class="space-y-4">
        <div 
          v-for="model in settingsStore.modelConfigs" 
          :key="model.id"
          class="border border-gray-200 rounded-lg p-4"
        >
          <div v-if="editingModel?.id === model.id" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">配置名称</label>
                <input v-model="editingModel.name" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">提供商</label>
                <select v-model="editingModel.provider" class="input-field">
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="google">Google</option>
                  <option value="custom">自定义</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
                <input v-model="editingModel.model_name" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                <input v-model="editingModel.api_key" type="password" class="input-field" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
                <input v-model="editingModel.base_url" type="text" class="input-field" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">适用文件类型</label>
                <div class="flex flex-wrap gap-2 mt-2 max-h-32 overflow-y-auto">
                  <button 
                    v-for="ft in fileTypeStore.fileTypes" 
                    :key="ft.id"
                    @click="toggleFileTypeForEditModel(ft.name)"
                    :class="[
                      'px-3 py-1 rounded-full text-sm transition-colors',
                      editingModel.file_types.includes(ft.name)
                        ? 'text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    ]"
                    :style="editingModel.file_types.includes(ft.name) ? { backgroundColor: ft.color } : {}"
                  >
                    {{ ft.display_name }}
                  </button>
                </div>
              </div>
            </div>
            <div class="flex items-center">
              <input v-model="editingModel.is_default" type="checkbox" :id="'isDefault-' + model.id" class="mr-2" />
              <label :for="'isDefault-' + model.id" class="text-sm text-gray-700">设为默认模型</label>
            </div>
            <div class="mt-4 border-t pt-4">
              <p class="text-sm font-medium text-gray-700 mb-3">AI用途配置（每种用途只能选择一个模型）</p>
              <div class="space-y-2">
                <div class="flex items-center">
                  <input v-model="editingModel.is_relation_completer" type="checkbox" :id="'isRelationCompleter-' + model.id" class="mr-2" />
                  <label :for="'isRelationCompleter-' + model.id" class="text-sm text-gray-700">作为补全关系图的AI</label>
                </div>
                <div class="flex items-center">
                  <input v-model="editingModel.is_topology_generator" type="checkbox" :id="'isTopologyGenerator-' + model.id" class="mr-2" />
                  <label :for="'isTopologyGenerator-' + model.id" class="text-sm text-gray-700">作为生成拓扑图的AI</label>
                </div>
                <div class="flex items-center">
                  <input v-model="editingModel.is_inspiration_generator" type="checkbox" :id="'isInspirationGenerator-' + model.id" class="mr-2" />
                  <label :for="'isInspirationGenerator-' + model.id" class="text-sm text-gray-700">作为生成创意的AI</label>
                </div>
              </div>
            </div>
            <div class="flex justify-end space-x-3 mt-4">
              <button @click="editingModel = null" class="btn-secondary">取消</button>
              <button @click="handleUpdateModel" class="btn-primary">保存</button>
            </div>
          </div>
          
          <div v-else class="flex justify-between items-start">
            <div>
              <div class="flex items-center space-x-2">
                <h3 class="font-semibold text-gray-800">{{ model.name }}</h3>
                <span v-if="model.is_default" class="px-2 py-0.5 bg-primary-100 text-primary-800 text-xs rounded-full">默认</span>
                <span v-if="model.is_relation_completer" class="px-2 py-0.5 bg-purple-100 text-purple-800 text-xs rounded-full">补全关系</span>
                <span v-if="model.is_topology_generator" class="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded-full">生成拓扑</span>
                <span v-if="model.is_inspiration_generator" class="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full">生成创意</span>
              </div>
              <p class="text-sm text-gray-500 mt-1">
                {{ model.provider }} / {{ model.model_name }}
              </p>
              <div v-if="model.file_types.length > 0" class="flex flex-wrap gap-1 mt-2">
                <span 
                  v-for="typeName in model.file_types" 
                  :key="typeName"
                  class="px-2 py-0.5 rounded text-xs text-white"
                  :style="{ backgroundColor: fileTypeStore.getTypeColor(typeName) }"
                >
                  {{ fileTypeStore.getTypeDisplayName(typeName) }}
                </span>
              </div>
            </div>
            <div class="flex space-x-2">
              <button @click="handleCopyModel(model)" class="text-green-600 hover:text-green-700" title="复制配置">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
              <button @click="handleEditModel(model)" class="text-primary-600 hover:text-primary-700" title="编辑">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button @click="handleDeleteModel(model.id)" class="text-red-500 hover:text-red-600" title="删除">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        <div v-if="settingsStore.modelConfigs.length === 0" class="text-center py-8 text-gray-500">
          还没有配置AI模型，点击上方按钮添加一个吧！
        </div>
      </div>
    </div>
    
    <div class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-lg font-semibold mb-4">关于</h2>
      <div class="text-gray-600">
        <p class="mb-2"><strong>Creative Master</strong> - AI驱动的创意灵感管理系统</p>
        <p class="text-sm">版本: 0.1.0</p>
        <p class="text-sm mt-2">
          <a href="https://github.com/chatabc/creative_master" target="_blank" class="text-primary-600 hover:text-primary-700">
            GitHub 仓库
          </a>
        </p>
      </div>
    </div>
  </div>
</template>
