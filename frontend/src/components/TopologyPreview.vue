<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { VueFlow, VueFlowProvider, type Node, type Edge } from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'

const props = defineProps<{
  nodes: Node[]
  edges: Edge[]
  previewId: string
}>()

const localNodes = ref<Node[]>([])
const localEdges = ref<Edge[]>([])

watch(() => props.nodes, (newNodes) => {
  localNodes.value = JSON.parse(JSON.stringify(newNodes))
}, { immediate: true, deep: true })

watch(() => props.edges, (newEdges) => {
  localEdges.value = JSON.parse(JSON.stringify(newEdges))
}, { immediate: true, deep: true })

onMounted(() => {
  localNodes.value = JSON.parse(JSON.stringify(props.nodes || []))
  localEdges.value = JSON.parse(JSON.stringify(props.edges || []))
})
</script>

<template>
  <VueFlowProvider>
    <VueFlow 
      :nodes="localNodes" 
      :edges="localEdges"
      :fit-view-on-init="true"
      :nodes-draggable="false"
      :nodes-connectable="false"
      :elements-selectable="false"
      :zoom-on-scroll="false"
      :pan-on-scroll="false"
      :min-zoom="0.2"
      :max-zoom="1.5"
    />
  </VueFlowProvider>
</template>

<style scoped>
:deep(.vue-flow) {
  background: transparent;
}
</style>
