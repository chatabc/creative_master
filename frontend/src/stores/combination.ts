import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { InspirationCombination, InspirationRelation, Creative } from '@/types'

const API_BASE = '/api/v1'

export const useCombinationStore = defineStore('combination', () => {
  const combinations = ref<InspirationCombination[]>([])
  const currentCombination = ref<InspirationCombination | null>(null)
  const currentRelations = ref<InspirationRelation[]>([])
  
  const fetchCombinations = async () => {
    try {
      const response = await axios.get(`${API_BASE}/combinations`)
      combinations.value = response.data
    } catch (error) {
      console.error('Failed to fetch combinations:', error)
    }
  }
  
  const getCombination = async (id: string): Promise<InspirationCombination | null> => {
    try {
      const response = await axios.get(`${API_BASE}/combinations/${id}`)
      return response.data
    } catch (error) {
      console.error('Failed to get combination:', error)
      return null
    }
  }
  
  const createCombination = async (data: {
    name: string
    description?: string
    inspiration_ids?: string[]
    sub_combination_ids?: string[]
    relations?: InspirationRelation[]
  }): Promise<InspirationCombination> => {
    try {
      const response = await axios.post(`${API_BASE}/combinations`, data)
      combinations.value.push(response.data)
      return response.data
    } catch (error) {
      console.error('Failed to create combination:', error)
      throw error
    }
  }
  
  const updateCombination = async (id: string, data: {
    name?: string
    description?: string
    inspiration_ids?: string[]
    sub_combination_ids?: string[]
    relations?: InspirationRelation[]
  }): Promise<InspirationCombination> => {
    try {
      const response = await axios.put(`${API_BASE}/combinations/${id}`, data)
      const index = combinations.value.findIndex(c => c.id === id)
      if (index > -1) {
        combinations.value[index] = response.data
      }
      if (currentCombination.value?.id === id) {
        currentCombination.value = response.data
      }
      return response.data
    } catch (error) {
      console.error('Failed to update combination:', error)
      throw error
    }
  }
  
  const deleteCombination = async (id: string) => {
    try {
      await axios.delete(`${API_BASE}/combinations/${id}`)
      combinations.value = combinations.value.filter(c => c.id !== id)
      if (currentCombination.value?.id === id) {
        currentCombination.value = null
      }
    } catch (error) {
      console.error('Failed to delete combination:', error)
      throw error
    }
  }
  
  const setCurrentCombination = (combination: InspirationCombination | null) => {
    currentCombination.value = combination
    currentRelations.value = combination?.relations || []
  }
  
  const addRelation = (relation: InspirationRelation) => {
    currentRelations.value.push(relation)
  }
  
  const removeRelation = (relationId: string) => {
    currentRelations.value = currentRelations.value.filter(
      r => r.id !== relationId
    )
  }
  
  const updateRelationDescription = (relationId: string, description: string) => {
    const relation = currentRelations.value.find(r => r.id === relationId)
    if (relation) {
      relation.description = description
    }
  }
  
  const clearCurrent = () => {
    currentCombination.value = null
    currentRelations.value = []
  }
  
  const saveCurrentRelations = async () => {
    if (!currentCombination.value) return
    await updateCombination(currentCombination.value.id, {
      relations: currentRelations.value
    })
  }
  
  const generateCreatives = async (count: number = 3): Promise<Creative[]> => {
    if (!currentCombination.value) return []
    
    try {
      const response = await axios.post(`${API_BASE}/creatives/generate`, {
        combination_id: currentCombination.value.id,
        count
      })
      return response.data
    } catch (error) {
      console.error('Failed to generate creatives:', error)
      throw error
    }
  }
  
  const getCreatives = async (combinationId?: string): Promise<Creative[]> => {
    try {
      const url = combinationId 
        ? `${API_BASE}/creatives?combination_id=${combinationId}`
        : `${API_BASE}/creatives`
      const response = await axios.get(url)
      return response.data
    } catch (error) {
      console.error('Failed to get creatives:', error)
      return []
    }
  }
  
  const getFlattenedInspirations = (combination: InspirationCombination): string[] => {
    const inspirations = [...combination.inspirations]
    for (const subId of combination.sub_combinations) {
      const sub = combinations.value.find(c => c.id === subId)
      if (sub) {
        inspirations.push(...getFlattenedInspirations(sub))
      }
    }
    return [...new Set(inspirations)]
  }
  
  return {
    combinations,
    currentCombination,
    currentRelations,
    fetchCombinations,
    getCombination,
    createCombination,
    updateCombination,
    deleteCombination,
    setCurrentCombination,
    addRelation,
    removeRelation,
    updateRelationDescription,
    clearCurrent,
    saveCurrentRelations,
    generateCreatives,
    getCreatives,
    getFlattenedInspirations
  }
})
