import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue')
    },
    {
      path: '/inspirations',
      name: 'inspirations',
      component: () => import('@/views/InspirationsView.vue')
    },
    {
      path: '/combine',
      name: 'combine',
      component: () => import('@/views/CombineView.vue')
    },
    {
      path: '/combinations',
      name: 'combinations',
      component: () => import('@/views/CombinationsView.vue')
    },
    {
      path: '/creatives',
      name: 'creatives',
      component: () => import('@/views/CreativesView.vue')
    },
    {
      path: '/creative-management',
      name: 'creative-management',
      component: () => import('@/views/CreativeManagementView.vue')
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue')
    }
  ]
})

export default router
