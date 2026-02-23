<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { computed, onMounted } from 'vue'
import { useInspirationStore } from '@/stores/inspiration'
import { useCreativeStore } from '@/stores/creative'
import { useCombinationStore } from '@/stores/combination'

const route = useRoute()
const inspirationStore = useInspirationStore()
const creativeStore = useCreativeStore()
const combinationStore = useCombinationStore()

onMounted(async () => {
  await Promise.all([
    inspirationStore.fetchInspirations(),
    creativeStore.fetchCreatives(),
    combinationStore.fetchCombinations()
  ])
})

const menuItems = [
  { path: '/', icon: 'home', label: '工作台' },
  { path: '/inspirations', icon: 'folder', label: '灵感库' },
  { path: '/combine', icon: 'link', label: '生成组合' },
  { path: '/combinations', icon: 'layers', label: '组合管理' },
  { path: '/creatives', icon: 'sparkles', label: '生成创意' },
  { path: '/creative-management', icon: 'layers', label: '创意管理' },
  { path: '/settings', icon: 'cog', label: '设置' },
]

const isActive = (path: string) => {
  return route.path === path
}

const stats = computed(() => ({
  inspirations: inspirationStore.inspirations.length,
  combinations: combinationStore.combinations.length,
  creatives: creativeStore.creatives.length
}))
</script>

<template>
  <aside class="fixed left-0 top-16 bottom-0 w-64 bg-white border-r border-gray-200 overflow-y-auto">
    <nav class="p-4 space-y-1">
      <RouterLink
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors',
          isActive(item.path)
            ? 'bg-primary-50 text-primary-600'
            : 'text-gray-600 hover:bg-gray-50'
        ]"
      >
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
    
    <div class="p-4 border-t border-gray-200 mt-4">
      <div class="text-sm text-gray-500">
        <p class="font-medium mb-2">快速统计</p>
        <div class="space-y-1">
          <div class="flex justify-between">
            <span>灵感数量:</span>
            <span class="font-medium text-gray-700">{{ stats.inspirations }}</span>
          </div>
          <div class="flex justify-between">
            <span>组合数量:</span>
            <span class="font-medium text-gray-700">{{ stats.combinations }}</span>
          </div>
          <div class="flex justify-between">
            <span>创意数量:</span>
            <span class="font-medium text-gray-700">{{ stats.creatives }}</span>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>
