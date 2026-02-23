<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useInspirationStore } from '@/stores/inspiration'
import { useCreativeStore } from '@/stores/creative'
import { useCombinationStore } from '@/stores/combination'

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

const stats = computed(() => ({
  totalInspirations: inspirationStore.inspirations.length,
  totalCombinations: combinationStore.combinations.length,
  totalCreatives: creativeStore.creatives.length,
  byType: {
    image: inspirationStore.inspirations.filter(i => i.type === 'image').length,
    code: inspirationStore.inspirations.filter(i => i.type === 'code').length,
    text: inspirationStore.inspirations.filter(i => i.type === 'text').length,
    video: inspirationStore.inspirations.filter(i => i.type === 'video').length,
    audio: inspirationStore.inspirations.filter(i => i.type === 'audio').length,
    document: inspirationStore.inspirations.filter(i => i.type === 'document').length,
    folder: inspirationStore.inspirations.filter(i => i.type === 'folder').length,
  }
}))

const recentInspirations = computed(() => 
  [...inspirationStore.inspirations]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)
)

const recentCreatives = computed(() => 
  [...creativeStore.creatives]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 3)
)
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">工作台</h1>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">总灵感数</p>
            <p class="text-3xl font-bold text-gray-800">{{ stats.totalInspirations }}</p>
          </div>
          <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">总组合数</p>
            <p class="text-3xl font-bold text-gray-800">{{ stats.totalCombinations }}</p>
          </div>
          <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">总创意数</p>
            <p class="text-3xl font-bold text-gray-800">{{ stats.totalCreatives }}</p>
          </div>
          <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-gray-500">图片灵感</p>
            <p class="text-3xl font-bold text-gray-800">{{ stats.byType.image }}</p>
          </div>
          <div class="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>
    </div>
    
    <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
      <div class="bg-white rounded-lg shadow p-4 text-center">
        <p class="text-2xl font-bold text-yellow-600">{{ stats.byType.code }}</p>
        <p class="text-sm text-gray-500">代码</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 text-center">
        <p class="text-2xl font-bold text-blue-600">{{ stats.byType.text }}</p>
        <p class="text-sm text-gray-500">文本</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 text-center">
        <p class="text-2xl font-bold text-red-600">{{ stats.byType.video }}</p>
        <p class="text-sm text-gray-500">视频</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 text-center">
        <p class="text-2xl font-bold text-purple-600">{{ stats.byType.audio }}</p>
        <p class="text-sm text-gray-500">音频</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 text-center">
        <p class="text-2xl font-bold text-pink-600">{{ stats.byType.document }}</p>
        <p class="text-sm text-gray-500">文档</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4 text-center">
        <p class="text-2xl font-bold text-gray-600">{{ stats.byType.folder }}</p>
        <p class="text-sm text-gray-500">文件夹</p>
      </div>
    </div>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-lg font-semibold mb-4">最近添加的灵感</h2>
        <div class="space-y-3">
          <div 
            v-for="insp in recentInspirations" 
            :key="insp.id"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div>
              <p class="font-medium text-gray-800">{{ insp.name }}</p>
              <p class="text-sm text-gray-500">{{ insp.type }}</p>
            </div>
            <span class="text-xs text-gray-400">
              {{ new Date(insp.created_at).toLocaleDateString() }}
            </span>
          </div>
          <div v-if="recentInspirations.length === 0" class="text-center py-8 text-gray-400">
            还没有灵感
          </div>
        </div>
      </div>
      
      <div class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-lg font-semibold mb-4">最近生成的创意</h2>
        <div class="space-y-3">
          <div 
            v-for="creative in recentCreatives" 
            :key="creative.id"
            class="p-3 bg-gray-50 rounded-lg"
          >
            <p class="font-medium text-gray-800">{{ creative.title }}</p>
            <p class="text-sm text-gray-500 line-clamp-2 mt-1">{{ creative.description }}</p>
          </div>
          <div v-if="recentCreatives.length === 0" class="text-center py-8 text-gray-400">
            还没有创意
          </div>
        </div>
      </div>
    </div>
    
    <div class="bg-gradient-to-r from-primary-500 to-purple-600 rounded-lg shadow-md p-8 text-white">
      <h2 class="text-2xl font-bold mb-4">开始创作</h2>
      <p class="mb-6 opacity-90">
        添加你的灵感素材，让AI帮你组合创意，生成独特的提示词
      </p>
      <div class="flex space-x-4">
        <RouterLink to="/inspirations" class="bg-white text-primary-600 px-6 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors">
          添加灵感
        </RouterLink>
        <RouterLink to="/combine" class="bg-white/20 text-white px-6 py-2 rounded-lg font-medium hover:bg-white/30 transition-colors">
          组合创意
        </RouterLink>
      </div>
    </div>
  </div>
</template>
