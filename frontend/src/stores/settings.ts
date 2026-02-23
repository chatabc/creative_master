import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { AIModelConfig, InspirationType } from '@/types'

const API_BASE = '/api/v1'

export const useSettingsStore = defineStore('settings', () => {
  const modelConfigs = ref<AIModelConfig[]>([])
  
  const fetchModelConfigs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/config/models`)
      modelConfigs.value = response.data
    } catch (error) {
      console.error('Failed to fetch model configs:', error)
    }
  }
  
  const getModelConfig = async (id: string): Promise<AIModelConfig | null> => {
    try {
      const response = await axios.get(`${API_BASE}/config/models/${id}`)
      return response.data
    } catch (error) {
      console.error('Failed to get model config:', error)
      return null
    }
  }
  
  const addModelConfig = async (data: {
    name: string
    provider: string
    model_name: string
    api_key: string
    base_url?: string
    file_types: InspirationType[]
    is_default: boolean
    is_relation_completer?: boolean
    is_topology_generator?: boolean
    is_inspiration_generator?: boolean
  }): Promise<AIModelConfig> => {
    try {
      const response = await axios.post(`${API_BASE}/config/models`, data)
      await fetchModelConfigs()
      return response.data
    } catch (error) {
      console.error('Failed to add model config:', error)
      throw error
    }
  }
  
  const updateModelConfig = async (id: string, data: {
    name: string
    provider: string
    model_name: string
    api_key: string
    base_url?: string
    file_types: InspirationType[]
    is_default: boolean
    is_relation_completer?: boolean
    is_topology_generator?: boolean
    is_inspiration_generator?: boolean
  }): Promise<AIModelConfig> => {
    try {
      const response = await axios.put(`${API_BASE}/config/models/${id}`, data)
      await fetchModelConfigs()
      return response.data
    } catch (error) {
      console.error('Failed to update model config:', error)
      throw error
    }
  }
  
  const deleteModelConfig = async (id: string) => {
    try {
      await axios.delete(`${API_BASE}/config/models/${id}`)
      modelConfigs.value = modelConfigs.value.filter(m => m.id !== id)
    } catch (error) {
      console.error('Failed to delete model config:', error)
      throw error
    }
  }
  
  return {
    modelConfigs,
    fetchModelConfigs,
    getModelConfig,
    addModelConfig,
    updateModelConfig,
    deleteModelConfig
  }
})
