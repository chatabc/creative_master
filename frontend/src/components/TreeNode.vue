<template>
  <div class="select-none">
    <div 
      class="flex items-center py-1 px-2 hover:bg-gray-100 rounded cursor-pointer"
      :style="{ paddingLeft: `${depth * 16 + 8}px` }"
    >
      <span 
        v-if="node.is_dir" 
        @click="toggleExpand"
        class="w-4 h-4 flex items-center justify-center text-gray-400 hover:text-gray-600"
      >
        <svg 
          :class="['w-3 h-3 transition-transform', isExpanded ? 'rotate-90' : '']" 
          fill="currentColor" 
          viewBox="0 0 20 20"
        >
          <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
        </svg>
      </span>
      <span v-else class="w-4"></span>
      
      <input 
        type="checkbox"
        :checked="isIgnored"
        @change="handleToggle"
        class="w-4 h-4 text-red-500 border-gray-300 rounded focus:ring-red-500 ml-1"
      />
      
      <span class="ml-2">
        <span v-if="node.is_dir" class="text-yellow-500">
          <svg class="w-4 h-4 inline" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
          </svg>
        </span>
        <span v-else class="text-gray-400">
          <svg class="w-4 h-4 inline" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd" />
          </svg>
        </span>
      </span>
      
      <span 
        :class="[
          'ml-1 text-sm truncate',
          isIgnored ? 'text-gray-400 line-through' : 'text-gray-700'
        ]"
        :title="node.name"
      >
        {{ node.name }}
      </span>
      
      <span v-if="!node.is_dir && node.size" class="ml-auto text-xs text-gray-400">
        {{ formatSize(node.size) }}
      </span>
    </div>
    
    <div v-if="node.is_dir && isExpanded && node.children">
      <TreeNode
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        :depth="depth + 1"
        :ignored-paths="ignoredPaths"
        @toggle-ignore="$emit('toggle-ignore', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, defineProps, defineEmits } from 'vue'

interface TreeNodeData {
  name: string
  path: string
  is_dir: boolean
  size?: number
  children?: TreeNodeData[]
}

const props = defineProps<{
  node: TreeNodeData
  depth?: number
  ignoredPaths: string[]
}>()

const emit = defineEmits<{
  (e: 'toggle-ignore', path: string): void
}>()

const depth = props.depth || 0
const isExpanded = ref(true)

const isIgnored = computed(() => props.ignoredPaths.includes(props.node.path))

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const handleToggle = () => {
  emit('toggle-ignore', props.node.path)
}

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}
</script>
