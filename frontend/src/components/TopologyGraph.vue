<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import type { InspirationRelation } from '@/types'

interface TopologyNode {
  id: string
  name: string
  type: string
  x: number
  y: number
}

interface TopologyEdge {
  id: string
  sourceId: string
  targetId: string
  relationType: string
  description: string
  customTypeId?: string | null
}

const props = defineProps<{
  nodes: TopologyNode[]
  edges: TopologyEdge[]
  customRelationTypes?: any[]
  editable?: boolean
  height?: number
}>()

const emit = defineEmits<{
  (e: 'selectNode', node: TopologyNode): void
  (e: 'selectEdge', edge: TopologyEdge): void
  (e: 'createRelation', sourceId: string, targetId: string): void
}>()

const selectedNode = ref<string | null>(null)
const connectingFrom = ref<string | null>(null)

const padding = 80

const bounds = computed(() => {
  if (props.nodes.length === 0) {
    return { minX: 0, minY: 0, maxX: 400, maxY: 300 }
  }
  
  const xs = props.nodes.map(n => n.x)
  const ys = props.nodes.map(n => n.y)
  
  const minX = Math.min(...xs) - padding
  const minY = Math.min(...ys) - padding
  const maxX = Math.max(...xs) + padding
  const maxY = Math.max(...ys) + padding
  
  return { minX, minY, maxX, maxY, width: maxX - minX, height: maxY - minY }
})

const viewBox = computed(() => {
  const b = bounds.value
  return `${b.minX} ${b.minY} ${b.width} ${b.height}`
})

function getNodeColor(type: string): string {
  const colors: Record<string, string> = {
    image: '#3b82f6',
    code: '#22c55e',
    text: '#eab308',
    video: '#ef4444',
    audio: '#a855f7',
    document: '#ec4899',
    folder: '#6b7280'
  }
  return colors[type] || '#6b7280'
}

function getEdgeColor(relationType: string, customTypeId?: string | null): string {
  if (relationType === 'custom' && customTypeId && props.customRelationTypes) {
    const customType = props.customRelationTypes.find(rt => rt.id === customTypeId)
    if (customType) return customType.style?.stroke || '#6b7280'
  }
  
  const colors: Record<string, string> = {
    primary: '#8b5cf6',
    parallel: '#22c55e',
    contrast: '#ef4444'
  }
  return colors[relationType] || '#6b7280'
}

function getEdgeLabel(relationType: string, customTypeId?: string | null): string {
  if (relationType === 'custom' && customTypeId && props.customRelationTypes) {
    const customType = props.customRelationTypes.find(rt => rt.id === customTypeId)
    if (customType) return customType.display_name || '自定义'
  }
  
  const labels: Record<string, string> = {
    primary: '主从',
    parallel: '平行',
    contrast: '对比'
  }
  return labels[relationType] || '关系'
}

function getNodeById(id: string): TopologyNode | undefined {
  return props.nodes.find(n => n.id === id)
}

function getEdgePath(edge: TopologyEdge): string {
  const source = getNodeById(edge.sourceId)
  const target = getNodeById(edge.targetId)
  
  if (!source || !target) return ''
  
  return `M ${source.x} ${source.y} L ${target.x} ${target.y}`
}

function getEdgeMidpoint(edge: TopologyEdge): { x: number; y: number } {
  const source = getNodeById(edge.sourceId)
  const target = getNodeById(edge.targetId)
  
  if (!source || !target) return { x: 0, y: 0 }
  
  return {
    x: (source.x + target.x) / 2,
    y: (source.y + target.y) / 2
  }
}

function getArrowPoints(edge: TopologyEdge): string {
  const source = getNodeById(edge.sourceId)
  const target = getNodeById(edge.targetId)
  
  if (!source || !target) return ''
  
  const dx = target.x - source.x
  const dy = target.y - source.y
  const len = Math.sqrt(dx * dx + dy * dy)
  if (len === 0) return ''
  
  const ux = dx / len
  const uy = dy / len
  
  const arrowSize = 10
  const nodeRadius = 50
  
  const endX = target.x - ux * nodeRadius
  const endY = target.y - uy * nodeRadius
  
  const p1x = endX - ux * arrowSize - uy * arrowSize
  const p1y = endY - uy * arrowSize + ux * arrowSize
  const p2x = endX - ux * arrowSize + uy * arrowSize
  const p2y = endY - uy * arrowSize - ux * arrowSize
  
  return `${p1x},${p1y} ${endX},${endY} ${p2x},${p2y}`
}

function getReverseArrowPoints(edge: TopologyEdge): string {
  const source = getNodeById(edge.sourceId)
  const target = getNodeById(edge.targetId)
  
  if (!source || !target) return ''
  
  const dx = source.x - target.x
  const dy = source.y - target.y
  const len = Math.sqrt(dx * dx + dy * dy)
  if (len === 0) return ''
  
  const ux = dx / len
  const uy = dy / len
  
  const arrowSize = 10
  const nodeRadius = 50
  
  const endX = source.x - ux * nodeRadius
  const endY = source.y - uy * nodeRadius
  
  const p1x = endX - ux * arrowSize - uy * arrowSize
  const p1y = endY - uy * arrowSize + ux * arrowSize
  const p2x = endX - ux * arrowSize + uy * arrowSize
  const p2y = endY - uy * arrowSize - ux * arrowSize
  
  return `${p1x},${p1y} ${endX},${endY} ${p2x},${p2y}`
}

const handleNodeClick = (node: TopologyNode) => {
  if (!props.editable) return
  
  if (connectingFrom.value === null) {
    connectingFrom.value = node.id
    selectedNode.value = node.id
  } else if (connectingFrom.value !== node.id) {
    emit('createRelation', connectingFrom.value, node.id)
    connectingFrom.value = null
    selectedNode.value = null
  } else {
    connectingFrom.value = null
    selectedNode.value = null
  }
}

const handleEdgeClick = (edge: TopologyEdge) => {
  if (props.editable) {
    emit('selectEdge', edge)
  }
}

const cancelConnecting = () => {
  connectingFrom.value = null
  selectedNode.value = null
}
</script>

<template>
  <div class="relative w-full h-full" :style="{ minHeight: `${height || 250}px` }">
    <svg 
      class="w-full h-full"
      :viewBox="viewBox"
      preserveAspectRatio="xMidYMid meet"
      @click.self="cancelConnecting"
    >
      <defs>
        <marker 
          id="arrowhead" 
          markerWidth="10" 
          markerHeight="7" 
          refX="9" 
          refY="3.5" 
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#6b7280" />
        </marker>
      </defs>
      
      <g class="edges">
        <g 
          v-for="edge in edges" 
          :key="edge.id"
          @click.stop="handleEdgeClick(edge)"
          :class="{ 'cursor-pointer': editable }"
        >
          <path
            :d="getEdgePath(edge)"
            :stroke="getEdgeColor(edge.relationType, edge.customTypeId)"
            stroke-width="2"
            fill="none"
            class="transition-all"
            :class="{ 'hover:stroke-width-4': editable }"
          />
          
          <polygon
            v-if="edge.relationType === 'primary' || edge.relationType === 'contrast'"
            :points="getArrowPoints(edge)"
            :fill="getEdgeColor(edge.relationType, edge.customTypeId)"
          />
          
          <polygon
            v-if="edge.relationType === 'contrast'"
            :points="getReverseArrowPoints(edge)"
            :fill="getEdgeColor(edge.relationType, edge.customTypeId)"
          />
          
          <g :transform="`translate(${getEdgeMidpoint(edge).x}, ${getEdgeMidpoint(edge).y})`">
            <rect
              :x="-30"
              :y="-10"
              width="60"
              height="20"
              rx="4"
              fill="white"
              stroke="#e5e7eb"
              stroke-width="1"
            />
            <text
              text-anchor="middle"
              dominant-baseline="middle"
              font-size="10"
              fill="#4b5563"
            >
              {{ getEdgeLabel(edge.relationType, edge.customTypeId) }}
            </text>
          </g>
        </g>
      </g>
      
      <g class="nodes">
        <g
          v-for="node in nodes"
          :key="node.id"
          :transform="`translate(${node.x}, ${node.y})`"
          @click.stop="handleNodeClick(node)"
          :class="{ 'cursor-pointer': editable }"
        >
          <rect
            :x="-50"
            :y="-20"
            width="100"
            height="40"
            rx="8"
            :fill="getNodeColor(node.type)"
            :stroke="selectedNode === node.id ? '#fbbf24' : 'transparent'"
            :stroke-width="selectedNode === node.id ? 3 : 0"
            class="transition-all"
          />
          <text
            text-anchor="middle"
            dominant-baseline="middle"
            fill="white"
            font-size="12"
            font-weight="500"
          >
            {{ node.name.length > 8 ? node.name.slice(0, 8) + '...' : node.name }}
          </text>
          <text
            :y="12"
            text-anchor="middle"
            fill="rgba(255,255,255,0.7)"
            font-size="8"
          >
            {{ node.type }}
          </text>
        </g>
      </g>
    </svg>
    
    <div 
      v-if="connectingFrom" 
      class="absolute top-2 left-2 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs"
    >
      点击另一个节点创建关系，或点击空白处取消
    </div>
    
    <div v-if="nodes.length === 0" class="absolute inset-0 flex items-center justify-center">
      <div class="text-center text-gray-400">
        <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
        </svg>
        <p class="text-sm">暂无拓扑图数据</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
svg {
  overflow: visible;
}
</style>
