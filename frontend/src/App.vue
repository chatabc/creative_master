<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <AppHeader />
    <div class="flex">
      <AppSidebar />
      <main class="flex-1 p-6 ml-64 mt-16">
        <RouterView />
      </main>
    </div>
  </div>
</template>
