import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { Creative } from '@/types'

const API_BASE = '/api/v1'

export const useCreativeStore = defineStore('creative', () => {
  const creatives = ref<Creative[]>([])
  
  const fetchCreatives = async (combinationId?: string) => {
    try {
      const url = combinationId 
        ? `${API_BASE}/creatives?combination_id=${combinationId}`
        : `${API_BASE}/creatives`
      const response = await axios.get(url)
      creatives.value = response.data
    } catch (error) {
      console.error('Failed to fetch creatives:', error)
    }
  }
  
  const regenerateCreatives = async (data: {
    combination_id: string
    feedback: string
    rating?: number
    count?: number
  }): Promise<Creative[]> => {
    try {
      const response = await axios.post(`${API_BASE}/creatives/regenerate`, data)
      creatives.value = [...creatives.value, ...response.data]
      return response.data
    } catch (error) {
      console.error('Failed to regenerate creatives:', error)
      throw error
    }
  }
  
  return {
    creatives,
    fetchCreatives,
    regenerateCreatives
  }
})
