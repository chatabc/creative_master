import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { GeneratedPrompt } from '@/types'

const API_BASE = '/api/v1'

export const usePromptStore = defineStore('prompt', () => {
  const prompts = ref<GeneratedPrompt[]>([])
  const currentPrompt = ref<GeneratedPrompt | null>(null)
  
  const generatePrompt = async (data: {
    creative_id: string
    inspiration_ids: string[]
    output_format?: string
    organize_files?: boolean
    output_folder?: string
  }): Promise<GeneratedPrompt> => {
    try {
      const response = await axios.post(`${API_BASE}/prompts/generate`, data)
      prompts.value.push(response.data)
      currentPrompt.value = response.data
      return response.data
    } catch (error) {
      console.error('Failed to generate prompt:', error)
      throw error
    }
  }
  
  const exportPrompt = async (promptId: string, format: string = 'markdown') => {
    try {
      const response = await axios.get(`${API_BASE}/prompts/${promptId}/export?format=${format}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `prompt_${promptId}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export prompt:', error)
      throw error
    }
  }
  
  return {
    prompts,
    currentPrompt,
    generatePrompt,
    exportPrompt
  }
})
