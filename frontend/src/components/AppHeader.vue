<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <header class="fixed top-0 left-0 right-0 h-16 bg-white shadow-sm z-50 flex items-center px-6">
    <div class="flex items-center space-x-2">
      <svg class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
      <span class="text-xl font-bold text-gray-800">Creative Master</span>
    </div>
    
    <nav class="ml-auto flex items-center space-x-6">
      <RouterLink to="/" class="text-gray-600 hover:text-primary-600 transition-colors">首页</RouterLink>
      <RouterLink to="/inspirations" class="text-gray-600 hover:text-primary-600 transition-colors">灵感库</RouterLink>
      <RouterLink to="/combine" class="text-gray-600 hover:text-primary-600 transition-colors">组合创意</RouterLink>
      <RouterLink to="/settings" class="text-gray-600 hover:text-primary-600 transition-colors">设置</RouterLink>
    </nav>
  </header>
</template>
