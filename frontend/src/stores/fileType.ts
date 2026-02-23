import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { CustomFileType } from '@/types'

const API_BASE = '/api/v1'

export interface ExtensionConflict {
  extension: string
  current_type: string
  current_display_name: string
}

export const useFileTypeStore = defineStore('fileType', () => {
  const fileTypes = ref<CustomFileType[]>([])
  
  const fetchFileTypes = async () => {
    try {
      const response = await axios.get(`${API_BASE}/file-types`)
      fileTypes.value = response.data
    } catch (error) {
      console.error('Failed to fetch file types:', error)
    }
  }
  
  const getFileType = (name: string): CustomFileType | undefined => {
    return fileTypes.value.find(ft => ft.name === name)
  }
  
  const checkConflicts = async (extensions: string[]): Promise<ExtensionConflict[]> => {
    try {
      const response = await axios.post(`${API_BASE}/file-types/check-conflicts`, { extensions })
      return response.data.conflicts || []
    } catch (error) {
      console.error('Failed to check conflicts:', error)
      return []
    }
  }
  
  const addFileType = async (data: {
    name: string
    display_name: string
    extensions: string[]
    icon?: string
    color?: string
    description?: string
    force_replace?: boolean
    extensions_to_replace?: string[]
  }): Promise<{ success: boolean; fileType?: CustomFileType; conflicts?: ExtensionConflict[] }> => {
    try {
      const response = await axios.post(`${API_BASE}/file-types`, data)
      
      if (response.data.status === 'conflict') {
        return { success: false, conflicts: response.data.conflicts }
      }
      
      if (response.data.file_type) {
        fileTypes.value.push(response.data.file_type)
        return { success: true, fileType: response.data.file_type }
      }
      
      return { success: true }
    } catch (error) {
      console.error('Failed to add file type:', error)
      throw error
    }
  }
  
  const updateFileType = async (typeId: string, data: {
    display_name?: string
    extensions?: string[]
    icon?: string
    color?: string
    description?: string
    text_mode?: boolean
    force_replace?: boolean
    extensions_to_replace?: string[]
  }): Promise<{ success: boolean; fileType?: CustomFileType; conflicts?: ExtensionConflict[] }> => {
    try {
      const response = await axios.put(`${API_BASE}/file-types/${typeId}`, data)
      
      if (response.data.status === 'conflict') {
        return { success: false, conflicts: response.data.conflicts }
      }
      
      if (response.data.file_type) {
        const index = fileTypes.value.findIndex(ft => ft.id === typeId)
        if (index > -1) {
          fileTypes.value[index] = response.data.file_type
        }
        return { success: true, fileType: response.data.file_type }
      }
      
      return { success: true }
    } catch (error) {
      console.error('Failed to update file type:', error)
      throw error
    }
  }
  
  const deleteFileType = async (typeId: string) => {
    await axios.delete(`${API_BASE}/file-types/${typeId}`)
    fileTypes.value = fileTypes.value.filter(ft => ft.id !== typeId)
  }
  
  const addExtensionToType = async (typeName: string, extension: string, forceReplace: boolean = false): Promise<{ success: boolean; fileType?: CustomFileType; conflict?: ExtensionConflict }> => {
    try {
      const response = await axios.post(`${API_BASE}/file-types/${typeName}/extensions`, { 
        extension,
        force_replace: forceReplace
      })
      
      if (response.data.status === 'conflict') {
        return { success: false, conflict: response.data.conflict }
      }
      
      if (response.data.file_type) {
        const index = fileTypes.value.findIndex(ft => ft.name === typeName)
        if (index > -1) {
          fileTypes.value[index] = response.data.file_type
        }
        return { success: true, fileType: response.data.file_type }
      }
      
      return { success: true }
    } catch (error) {
      console.error('Failed to add extension:', error)
      throw error
    }
  }
  
  const removeExtensionFromType = async (typeName: string, extension: string) => {
    const response = await axios.delete(`${API_BASE}/file-types/${typeName}/extensions/${extension}`)
    const index = fileTypes.value.findIndex(ft => ft.name === typeName)
    if (index > -1) {
      fileTypes.value[index] = response.data
    }
    return response.data
  }
  
  const resetToDefault = async () => {
    const response = await axios.post(`${API_BASE}/file-types/reset`)
    fileTypes.value = response.data
    return response.data
  }
  
  const detectType = (filename: string): string => {
    const ext = '.' + filename.split('.').pop()?.toLowerCase()
    for (const ft of fileTypes.value) {
      if (ft.extensions.includes(ext)) {
        return ft.name
      }
    }
    return 'other'
  }
  
  const getTypeColor = (typeName: string): string => {
    const ft = getFileType(typeName)
    return ft?.color || '#6b7280'
  }
  
  const getTypeDisplayName = (typeName: string): string => {
    const ft = getFileType(typeName)
    return ft?.display_name || typeName
  }
  
  const isTextMode = (typeName: string): boolean => {
    const ft = getFileType(typeName)
    return ft?.text_mode || false
  }
  
  const getTextModeTypes = (): string[] => {
    return fileTypes.value.filter(ft => ft.text_mode).map(ft => ft.name)
  }
  
  return {
    fileTypes,
    fetchFileTypes,
    getFileType,
    checkConflicts,
    addFileType,
    updateFileType,
    deleteFileType,
    addExtensionToType,
    removeExtensionFromType,
    resetToDefault,
    detectType,
    getTypeColor,
    getTypeDisplayName,
    isTextMode,
    getTextModeTypes
  }
})
