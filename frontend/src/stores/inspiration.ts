import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import type { Inspiration } from '@/types'

const API_BASE = '/api/v1'

export const useInspirationStore = defineStore('inspiration', () => {
  const inspirations = ref<Inspiration[]>([])
  
  const fetchInspirations = async () => {
    try {
      const response = await axios.get(`${API_BASE}/inspirations`)
      inspirations.value = response.data
    } catch (error) {
      console.error('Failed to fetch inspirations:', error)
    }
  }
  
  const getInspiration = (id: string): Inspiration | undefined => {
    return inspirations.value.find(i => i.id === id)
  }
  
  const addInspiration = async (data: {
    source_path: string
    name?: string
    tags?: string[]
    copy_file?: boolean
    file_type?: string
  }) => {
    try {
      const response = await axios.post(`${API_BASE}/inspirations`, data)
      inspirations.value.push(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to add inspiration:', error)
      throw error
    }
  }
  
  const uploadFile = async (file: File, options?: {
    name?: string
    tags?: string[]
    file_type?: string
  }): Promise<Inspiration> => {
    const formData = new FormData()
    formData.append('file', file)
    if (options?.name) formData.append('name', options.name)
    if (options?.tags) formData.append('tags', options.tags.join(','))
    if (options?.file_type) formData.append('file_type', options.file_type)
    
    const response = await axios.post(`${API_BASE}/inspirations/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    inspirations.value.push(response.data)
    return response.data
  }
  
  const uploadFiles = async (files: (File | FileList)[], tags?: string[]): Promise<Inspiration[]> => {
    const formData = new FormData()
    
    const filesArray = files instanceof FileList ? Array.from(files) : files
    filesArray.forEach(file => formData.append('files', file))
    if (tags) formData.append('tags', tags.join(','))
    
    if (files instanceof FileList) {
      formData.append('file_list', 'true')
    }
    
    const response = await axios.post(`${API_BASE}/inspirations/upload-batch`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    inspirations.value.push(...response.data)
    return response.data
  }
  
  const summarizeInspiration = async (id: string) => {
    try {
      const response = await axios.post(`${API_BASE}/inspirations/${id}/summarize`)
      const index = inspirations.value.findIndex(i => i.id === id)
      if (index > -1) {
        inspirations.value[index].summary = response.data.summary
      }
      return response.data
    } catch (error) {
      console.error('Failed to summarize inspiration:', error)
      throw error
    }
  }
  
  const deleteInspiration = async (id: string) => {
    try {
      await axios.delete(`${API_BASE}/inspirations/${id}`)
      inspirations.value = inspirations.value.filter(i => i.id !== id)
    } catch (error) {
      console.error('Failed to delete inspiration:', error)
      throw error
    }
  }
  
  const filteredInspirations = (type?: string, query?: string) => {
    let result = inspirations.value
    
    if (type) {
      result = result.filter(i => i.type === type)
    }
    
    if (query) {
      const q = query.toLowerCase()
      result = result.filter(i => 
        i.name.toLowerCase().includes(q) ||
        i.tags.some(t => t.toLowerCase().includes(q)) ||
        i.summary?.toLowerCase().includes(q)
      )
    }
    
    return result
  }
  
  return {
    inspirations,
    fetchInspirations,
    getInspiration,
    addInspiration,
    uploadFile,
    uploadFiles,
    summarizeInspiration,
    deleteInspiration,
    filteredInspirations
  }
})
