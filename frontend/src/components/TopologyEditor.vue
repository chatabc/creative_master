<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { VueFlow, useVueFlow, type Node, type Edge, MarkerType } from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import type { InspirationRelation } from '@/types'

const props = defineProps<{
  initialNodes: Node[]
  initialEdges: Edge[]
  initialRelations: InspirationRelation[]
  customRelationTypes: any[]
}>()

const emit = defineEmits<{
  (e: 'update:nodes', nodes: Node[]): void
  (e: 'update:edges', edges: Edge[]): void
  (e: 'update:relations', relations: InspirationRelation[]): void
}>()

const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])
const relations = ref<InspirationRelation[]>([])

const { onConnect, onEdgeClick, addEdges } = useVueFlow()

const showRelationTypeSelector = ref(false)
const pendingConnection = ref<{ source: string; target: string } | null>(null)

function getEdgeConfig(relationType: string, customTypeId?: string) {
  if (relationType === 'custom' && customTypeId) {
    const customType = props.customRelationTypes.find(rt => rt.id === customTypeId)
    if (customType) {
      return {
        style: customType.style || { stroke: '#6b7280', strokeWidth: 2 },
        markerEnd: customType.style?.markerEnd === 'arrow' ? MarkerType.ArrowClosed : undefined,
        markerStart: customType.style?.markerStart === 'arrow' ? MarkerType.ArrowClosed : undefined
      }
    }
  }
  
  const configs: Record<string, any> = {
    primary: {
      style: { stroke: '#8b5cf6', strokeWidth: 2 },
      markerEnd: MarkerType.ArrowClosed,
      markerStart: undefined
    },
    parallel: {
      style: { stroke: '#22c55e', strokeWidth: 2 },
      markerEnd: undefined,
      markerStart: undefined
    },
    contrast: {
      style: { stroke: '#ef4444', strokeWidth: 2 },
      markerEnd: MarkerType.ArrowClosed,
      markerStart: MarkerType.ArrowClosed
    }
  }
  return configs[relationType] || configs.parallel
}

function getRelationLabel(rel: InspirationRelation): string {
  if (rel.relation_type === 'custom' && rel.custom_type_id) {
    const customType = props.customRelationTypes.find(rt => rt.id === rel.custom_type_id)
    if (customType) {
      return customType.display_name || '自定义'
    }
  }
  
  const labels: Record<string, string> = {
    primary: '主从',
    parallel: '平行',
    contrast: '对比'
  }
  return labels[rel.relation_type] || '关系'
}

onConnect((params) => {
  pendingConnection.value = {
    source: params.source,
    target: params.target
  }
  showRelationTypeSelector.value = true
})

onEdgeClick(({ edge }) => {
  const index = edges.value.findIndex(e => e.id === edge.id)
  if (index > -1) {
    const currentDesc = edges.value[index].data?.description || ''
    const newLabel = prompt('编辑关系描述:', currentDesc)
    if (newLabel !== null) {
      const rel = edges.value[index].data
      if (rel) {
        rel.description = newLabel
        const relationLabel = getRelationLabel(rel)
        edges.value[index].label = `${relationLabel}${newLabel ? ': ' + newLabel : ''}`
        relations.value[index].description = newLabel
        emitUpdate()
      }
    }
  }
})

const handleSelectRelationType = (type: string, customTypeId?: string) => {
  if (!pendingConnection.value) return
  
  const edgeConfig = getEdgeConfig(type, customTypeId)
  const relLabel = type === 'custom' && customTypeId 
    ? (props.customRelationTypes.find(rt => rt.id === customTypeId)?.display_name || '自定义')
    : { primary: '主从', parallel: '平行', contrast: '对比' }[type] || '关系'
  
  const relId = `rel-${Date.now()}`
  const newRel: InspirationRelation = {
    id: relId,
    source_id: pendingConnection.value.source,
    target_id: pendingConnection.value.target,
    relation_type: type,
    custom_type_id: customTypeId || null,
    description: '',
    created_at: new Date().toISOString()
  }
  
  edges.value.push({
    id: relId,
    source: pendingConnection.value.source,
    target: pendingConnection.value.target,
    label: relLabel,
    type: 'smoothstep',
    style: edgeConfig.style,
    markerEnd: edgeConfig.markerEnd,
    markerStart: edgeConfig.markerStart,
    animated: type === 'primary',
    data: newRel,
    labelStyle: { fill: '#374151', fontWeight: 500, fontSize: '11px' },
    labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
    labelBgPadding: [4, 4] as [number, number],
    labelBgBorderRadius: 4
  })
  
  relations.value.push(newRel)
  
  showRelationTypeSelector.value = false
  pendingConnection.value = null
  
  emitUpdate()
}

const emitUpdate = () => {
  emit('update:nodes', nodes.value)
  emit('update:edges', edges.value)
  emit('update:relations', relations.value)
}

watch(() => props.initialNodes, (newNodes) => {
  nodes.value = JSON.parse(JSON.stringify(newNodes))
}, { immediate: true, deep: true })

watch(() => props.initialEdges, (newEdges) => {
  edges.value = JSON.parse(JSON.stringify(newEdges))
}, { immediate: true, deep: true })

watch(() => props.initialRelations, (newRelations) => {
  relations.value = JSON.parse(JSON.stringify(newRelations))
}, { immediate: true, deep: true })

onMounted(() => {
  nodes.value = JSON.parse(JSON.stringify(props.initialNodes))
  edges.value = JSON.parse(JSON.stringify(props.initialEdges))
  relations.value = JSON.parse(JSON.stringify(props.initialRelations))
})
</script>

<template>
  <div class="relative">
    <div class="h-[500px] border border-gray-200 rounded-lg">
      <VueFlow 
        v-if="nodes.length > 0"
        :nodes="nodes" 
        :edges="edges"
        fit-view-on-init
      />
    </div>
    
    <div class="mt-4 flex items-center justify-between">
      <div class="flex items-center space-x-4 text-sm text-gray-500">
        <div class="flex items-center">
          <div class="w-8 h-0.5 bg-purple-500 mr-2" style="border-right: 6px solid #8b5cf6; border-top: 4px solid transparent; border-bottom: 4px solid transparent;"></div>
          <span>主从关系</span>
        </div>
        <div class="flex items-center">
          <div class="w-8 h-0.5 bg-green-500 mr-2"></div>
          <span>平行关系</span>
        </div>
        <div class="flex items-center">
          <div class="w-8 h-0.5 bg-red-500 mr-2" style="border-left: 6px solid #ef4444; border-right: 6px solid #ef4444; border-top: 4px solid transparent; border-bottom: 4px solid transparent;"></div>
          <span>对比关系</span>
        </div>
      </div>
      
      <div class="text-sm text-gray-500">
        拖动节点调整位置，连接节点创建关系，点击连线编辑描述
      </div>
    </div>
    
    <div v-if="showRelationTypeSelector" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 w-96">
        <h3 class="text-lg font-semibold mb-4">选择关系类型</h3>
        <div class="space-y-2">
          <button 
            @click="handleSelectRelationType('primary')"
            class="w-full p-3 text-left border rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors"
          >
            <div class="flex items-center space-x-3">
              <div class="w-4 h-4 rounded-full bg-purple-500"></div>
              <div>
                <div class="font-medium">主从关系</div>
                <div class="text-xs text-gray-500">一个元素主导，另一个从属</div>
              </div>
            </div>
          </button>
          <button 
            @click="handleSelectRelationType('parallel')"
            class="w-full p-3 text-left border rounded-lg hover:bg-green-50 hover:border-green-300 transition-colors"
          >
            <div class="flex items-center space-x-3">
              <div class="w-4 h-4 rounded-full bg-green-500"></div>
              <div>
                <div class="font-medium">平行关系</div>
                <div class="text-xs text-gray-500">两个元素地位平等</div>
              </div>
            </div>
          </button>
          <button 
            @click="handleSelectRelationType('contrast')"
            class="w-full p-3 text-left border rounded-lg hover:bg-red-50 hover:border-red-300 transition-colors"
          >
            <div class="flex items-center space-x-3">
              <div class="w-4 h-4 rounded-full bg-red-500"></div>
              <div>
                <div class="font-medium">对比关系</div>
                <div class="text-xs text-gray-500">两个元素形成对比</div>
              </div>
            </div>
          </button>
          
          <div v-if="customRelationTypes.length > 0" class="border-t pt-2 mt-2">
            <p class="text-xs text-gray-500 mb-2">自定义关系类型</p>
            <button 
              v-for="rt in customRelationTypes" 
              :key="rt.id"
              @click="handleSelectRelationType('custom', rt.id)"
              class="w-full p-3 text-left border rounded-lg hover:bg-gray-50 transition-colors mb-1"
            >
              <div class="flex items-center space-x-3">
                <div class="w-4 h-4 rounded-full" :style="{ backgroundColor: rt.style?.stroke || '#6b7280' }"></div>
                <div>
                  <div class="font-medium">{{ rt.display_name }}</div>
                  <div v-if="rt.description" class="text-xs text-gray-500">{{ rt.description }}</div>
                </div>
              </div>
            </button>
          </div>
        </div>
        <div class="mt-4 flex justify-end">
          <button 
            @click="showRelationTypeSelector = false; pendingConnection = null"
            class="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
