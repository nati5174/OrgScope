<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch, useId } from 'vue'
import type { Organization } from '../engine/organization'
import type { VisibleNode } from '../engine/explorer'
import { CARD_HEIGHT, CARD_WIDTH, layoutTree } from '../engine/treeLayout'
import EmployeeCard from './EmployeeCard.vue'
const props = defineProps<{ org: Organization; nodes: VisibleNode[]; selected: string; focusId: string; expanded: Set<string>; pages: Map<string, number>; pageSize: number }>()
defineEmits<{ select: [id: string]; toggle: [id: string]; page: [id: string, delta: number]; focus: [id: string] }>()
const viewport = ref<HTMLElement>(), scale = ref(1), x = ref(20), y = ref(20), dragging = ref(false)
const helpId = useId()
let layoutComputations = 0
let anchorId = props.focusId
const layout = computed(() => ({ ...layoutTree(props.nodes), revision: ++layoutComputations }))
let observer: ResizeObserver | undefined, initialized = false
let drag: { pointer: number; x: number; y: number; originX: number; originY: number } | null = null
const size = ref({ width: 0, height: 0 })
function fit() {
  if (!size.value.width || !size.value.height || !layout.value.nodes.length) return
  scale.value = Math.max(.08, Math.min(1, (size.value.width - 32) / layout.value.width, (size.value.height - 100) / layout.value.height))
  x.value = (size.value.width - layout.value.width * scale.value) / 2
  y.value = (size.value.height - 64 - layout.value.height * scale.value) / 2
}
function reset() {
  scale.value = 1
  const root = layout.value.nodes.find(n => n.id === props.focusId)
  x.value = 32 - (root?.x ?? 0); y.value = size.value.height / 2 - ((root?.y ?? 0) + CARD_HEIGHT / 2)
}
function zoom(multiplier: number) {
  const next = Math.max(.08, Math.min(1.8, scale.value * multiplier)), ratio = next / scale.value
  x.value = size.value.width / 2 - (size.value.width / 2 - x.value) * ratio
  y.value = size.value.height / 2 - (size.value.height / 2 - y.value) * ratio; scale.value = next
}
function panStart(event: PointerEvent) {
  if (event.button !== 0 || (event.target as Element).closest('button, article, select')) return
  drag = { pointer: event.pointerId, x: event.clientX, y: event.clientY, originX: x.value, originY: y.value }
  dragging.value = true; viewport.value!.setPointerCapture(event.pointerId)
}
function panMove(event: PointerEvent) { if (drag) { x.value = drag.originX + event.clientX - drag.x; y.value = drag.originY + event.clientY - drag.y } }
function stop() { drag = null; dragging.value = false }
function wheel(event: WheelEvent) {
  if (event.ctrlKey || event.metaKey) { event.preventDefault(); zoom(event.deltaY < 0 ? 1.1 : 1 / 1.1) }
  else { event.preventDefault(); x.value -= event.deltaX; y.value -= event.deltaY }
}
function keyPan(event: KeyboardEvent) {
  if (event.target !== viewport.value) return
  const vectors: Record<string, [number, number]> = { ArrowDown: [0, -60], ArrowUp: [0, 60], ArrowRight: [-60, 0], ArrowLeft: [60, 0] }
  if (vectors[event.key]) { event.preventDefault(); const [dx, dy] = vectors[event.key]; x.value += dx; y.value += dy }
  if (event.key === 'Home') { event.preventDefault(); fit() }
}
function frameInitial() {
  fit()
  // Automatic framing must not shrink compact-card text below a readable size.
  // Explicit Fit still shows the complete tree; pan/zoom retain their behavior.
  if (size.value.width < 500 || scale.value < .85) reset()
}
watch(() => props.focusId, async id => { anchorId = id; await nextTick(); frameInitial() })
// Anchor the current root during expansion so a reflow does not jump the camera.
watch(layout, (next, previous) => {
  const before = previous?.nodes.find(n => n.id === anchorId), after = next.nodes.find(n => n.id === anchorId)
  if (before && after) { x.value += (before.x - after.x) * scale.value; y.value += (before.y - after.y) * scale.value }
})
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    size.value = { width: entry.contentRect.width, height: entry.contentRect.height }
    if (!initialized && entry.contentRect.width > 0) { frameInitial(); initialized = true }
  })
  observer.observe(viewport.value!)
  viewport.value!.addEventListener('wheel', wheel, { passive: false })
})
onBeforeUnmount(() => { observer?.disconnect(); viewport.value?.removeEventListener('wheel', wheel) })
function anchorOn(id: string) { anchorId = id }
defineExpose({ fit, reset, frameInitial, layout, anchorOn })
</script>
<template>
  <div class="canvas-shell">
    <div ref="viewport" class="org-canvas" :class="{ dragging }" tabindex="0" role="region" aria-label="Scrollable organization chart. Use arrow keys to pan or drag the background." :aria-describedby="helpId" @pointerdown="panStart" @pointermove="panMove" @pointerup="stop" @pointercancel="stop" @lostpointercapture="stop" @keydown="keyPan">
      <div class="chart-world" :style="{ width: `${layout.width}px`, height: `${layout.height}px`, transform: `translate(${x}px, ${y}px) scale(${scale})` }" :data-scale="scale" :data-layout-revision="layout.revision" :data-layout-width="layout.width" :data-layout-height="layout.height">
        <svg aria-hidden="true" class="chart-links" :width="layout.width" :height="layout.height"><path v-for="link in layout.connectors" :key="link.id" :d="link.path" fill="none" stroke="#94a3b8" stroke-width="1.5" /></svg>
        <div v-for="node in layout.nodes" :key="node.id" class="chart-node" :style="{ left: `${node.x}px`, top: `${node.y}px`, width: `${CARD_WIDTH}px`, height: `${CARD_HEIGHT}px` }">
          <EmployeeCard :employee="org.employees.get(node.id)!" :selected="selected === node.id" :expanded="expanded.has(node.id)" :reports="org.children.get(node.id)!.length" :descendants="org.metrics.get(node.id)!.descendantCount" :non-leaf-descendants="org.metrics.get(node.id)!.nonLeafDescendantCount" :page="pages.get(node.id) ?? 0" :page-count="Math.ceil(org.children.get(node.id)!.length / pageSize)" :is-root="org.employees.get(node.id)!.managerId === null" @select="$emit('select', node.id)" @toggle="$emit('toggle', node.id)" @page="delta => $emit('page', node.id, delta)" @focus="$emit('focus', node.id)" />
        </div>
      </div>
    </div>
    <div class="canvas-legend"><span class="legend-dot"></span>Org chart <span class="text-slate-400">/</span> {{ nodes.length }} visible</div>
    <div class="canvas-toolbar" role="toolbar" aria-label="Chart navigation"><button aria-label="Zoom out" :disabled="scale <= .08" @click="zoom(1 / 1.15)">−</button><output aria-label="Chart zoom">{{ Math.round(scale * 100) }}%</output><button aria-label="Zoom in" :disabled="scale >= 1.8" @click="zoom(1.15)">+</button><span class="toolbar-divider"></span><button @click="fit">Fit to view</button><button @click="reset">Reset view</button></div>
    <span :id="helpId" class="sr-only">Drag or scroll to pan. Use zoom controls or control plus wheel to zoom. Arrow keys pan when the chart region has focus; Home fits the tree.</span>
  </div>
</template>
