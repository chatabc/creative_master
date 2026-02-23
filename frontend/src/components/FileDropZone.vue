<script setup lang="ts">
import { ref, computed } from 'vue'
import { useFileTypeStore } from '@/stores/fileType'

const props = defineProps<{
  multiple?: boolean
  accept?: string
}>()

const emit = defineEmits<{
  (e: 'files-selected', files: (File | FileList)[]): void
}>()

const fileTypeStore = useFileTypeStore()

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFiles = ref<(File | FileList)[]>([])

const dragOver = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = true
}

const dragLeave = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
}

const drop = async (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  
  const items = Array.from(e.dataTransfer?.items || [])
  
  for (const item of items) {
    if (item.kind === 'file') {
      const entry = item.webkitGetAsEntry?.()
      if (entry) {
        if (entry.isDirectory) {
          const files = await getFilesFromDirectory(entry as FileSystemDirectoryEntry)
          if (files.length > 0) {
            if (props.multiple) {
              selectedFiles.value = [files as FileList]
            } else {
              selectedFiles.value = [files[0]]
            }
            emit('files-selected', selectedFiles.value)
            return
          }
        } else {
          const file = item.getAsFile?.()
          if (file) {
            if (props.multiple) {
              selectedFiles.value = [file]
            } else {
              selectedFiles.value = [file]
            }
            emit('files-selected', selectedFiles.value)
            return
          }
        }
      }
    }
  }
  
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length > 0) {
    if (props.multiple) {
      selectedFiles.value = files
    } else {
      selectedFiles.value = [files[0]]
    }
    emit('files-selected', selectedFiles.value)
  }
}

async function getFilesFromDirectory(directoryEntry: FileSystemDirectoryEntry): Promise<File[]> {
  const files: File[] = []
  
  async function readDirectory(entry: FileSystemDirectoryEntry, path: string = ''): Promise<void> {
    const reader = entry.createReader()
    const entries = await new Promise<FileSystemEntry[]>((resolve, reject) => {
      reader.readEntries(resolve, reject)
    })
    
    for (const entry of entries) {
      if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === '__pycache__') {
        continue
      }
      
      const fullPath = path + entry.name
      
      if (entry.isDirectory) {
        await readDirectory(entry as FileSystemDirectoryEntry, fullPath + '/')
      } else {
        const file = await new Promise<File>((resolve, reject) => {
          (entry as FileSystemFileEntry).file(resolve, reject)
        })
        files.push(file)
      }
    }
  }
  
  await readDirectory(directoryEntry)
  return files
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const onFileSelect = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = Array.from(target.files || [])
  
  if (files.length > 0) {
    if (props.multiple) {
      selectedFiles.value = files
    } else {
      selectedFiles.value = [files[0]]
    }
    emit('files-selected', selectedFiles.value)
  }
}

const getFileTypeColor = (filename: string): string => {
  return fileTypeStore.getTypeColor(fileTypeStore.detectType(filename))
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const clearFiles = () => {
  selectedFiles.value = []
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

defineExpose({
  clearFiles,
  selectedFiles
})
</script>

<template>
  <div class="w-full">
    <div
      @dragover="dragOver"
      @dragleave="dragLeave"
      @drop="drop"
      @click="triggerFileInput"
      :class="[
        'relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200',
        isDragging 
          ? 'border-primary-500 bg-primary-50' 
          : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
      ]"
    >
      <input
        ref="fileInput"
        type="file"
        :multiple="multiple"
        :webkitdirectory="multiple ? undefined : true"
        :accept="accept"
        @change="onFileSelect"
        class="hidden"
      />
      
      <div class="flex flex-col items-center">
        <svg 
          :class="[
            'w-12 h-12 mb-4 transition-colors',
            isDragging ? 'text-primary-500' : 'text-gray-400'
          ]" 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path 
            stroke-linecap="round" 
            stroke-linejoin="round" 
            stroke-width="2" 
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3 3v12" 
          />
        </svg>
        
        <p class="text-lg font-medium text-gray-700 mb-1">
          {{ isDragging ? '松开以上传文件' : (multiple ? '拖拽文件/文件夹到此处' : '拖拽文件/文件夹到此处') }}
        </p>
        <p class="text-sm text-gray-500">
          或 <span class="text-primary-600 font-medium">{{ multiple ? '点击选择文件/文件夹' : '点击选择文件/文件夹' }}</span>
        </p>
        <p class="text-xs text-gray-400 mt-2">
          支持所有文件类型：图片、代码、视频、音频、模型文件等，也支持文件夹上传
        </p>
      </div>
    </div>
    
    <div v-if="selectedFiles.length > 0" class="mt-4">
      <div class="flex justify-between items-center mb-2">
        <span class="text-sm font-medium text-gray-700">
          已选择 {{ selectedFiles.length }} 个{{ selectedFiles[0] instanceof FileList ? '文件夹' : '文件' }}
        </span>
        <button 
          @click="clearFiles"
          class="text-sm text-red-500 hover:text-red-600"
        >
          清除
        </button>
      </div>
      
      <div class="space-y-2 max-h-48 overflow-y-auto">
        <div 
          v-for="(file, index) in selectedFiles" 
          :key="index"
          class="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
        >
          <div class="flex items-center space-x-3">
            <div 
              class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
              :style="{ backgroundColor: getFileTypeColor(file instanceof File ? file.name : 'FOLDER') }"
            >
              {{ file instanceof File ? file.name.split('.').pop()?.toUpperCase().slice(0, 3) || 'FILE' : 'DIR' }}
            </div>
            <div>
              <p class="text-sm font-medium text-gray-800 truncate max-w-xs">
                {{ file instanceof File ? file.name : '文件夹: ' + (file as any).name }}
              </p>
              <p class="text-xs text-gray-500">
                {{ file instanceof File ? formatFileSize(file.size) : (file as any).length + ' 个文件' }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
