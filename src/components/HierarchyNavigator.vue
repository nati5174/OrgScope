<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'
import type { Organization } from '../engine/organization'
import { searchEmployees } from '../engine/organization'
import { navigatorRows, type NavigatorRow } from '../engine/navigator'
const props = defineProps<{ org: Organization; selected: string; expanded: Set<string>; pages: Map<string, number>; pageSize: number }>()
const emit = defineEmits<{ select: [id: string]; toggle: [id: string]; page: [id: string, delta: number]; close: [] }>()
const query = ref(''), scroll = ref(0), container = ref<HTMLElement>(), containerHeight = ref(500), active = ref(`employee:${props.selected}`)
const searchId = useId()
const rows = computed(() => navigatorRows(props.org, props.expanded, props.pages, props.pageSize))
const matches = computed(() => searchEmployees(props.org, query.value))
const rowHeight = 50, overscan = 4
const start = computed(() => Math.max(0, Math.floor(scroll.value / rowHeight) - overscan))
const virtualRows = computed(() => rows.value.slice(start.value, start.value + Math.ceil(containerHeight.value / rowHeight) + overscan * 2))
const activeVisible = computed(() => virtualRows.value.some(row => row.key === active.value))
let observer: ResizeObserver | undefined
async function revealSelected(keyboard = false) {
  await nextTick()
  const index = rows.value.findIndex(row => row.kind === 'employee' && row.id === props.selected)
  if (index >= 0 && container.value) {
    const top = index * rowHeight
    if (top < container.value.scrollTop || top + rowHeight > container.value.scrollTop + containerHeight.value) container.value.scrollTop = Math.max(0, top - containerHeight.value / 2)
    scroll.value = container.value.scrollTop
    if (keyboard && container.value.offsetHeight > 0) { await nextTick(); container.value.querySelector<HTMLElement>(`[data-nav-row="${CSS.escape(props.selected)}"]`)?.focus({ preventScroll: true }) }
  }
}
watch(() => props.selected, () => { active.value = `employee:${props.selected}`; void revealSelected() })
function choose(id: string, keyboard = false) { query.value = ''; active.value = `employee:${id}`; emit('select', id); void revealSelected(keyboard) }
async function focusRow(index: number) {
  const row = rows.value[Math.max(0, Math.min(rows.value.length - 1, index))]
  if (!row || !container.value) return
  active.value = row.key
  const rowIndex = rows.value.indexOf(row), top = rowIndex * rowHeight
  if (top < container.value.scrollTop || top + rowHeight > container.value.scrollTop + containerHeight.value) container.value.scrollTop = top
  scroll.value = container.value.scrollTop; await nextTick()
  container.value.querySelector<HTMLElement>(`[data-nav-key="${CSS.escape(row.key)}"]`)?.focus({ preventScroll: true })
}
function key(event: KeyboardEvent, row: NavigatorRow) {
  const index = rows.value.findIndex(value => value.key === row.key)
  const handled = ['ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'Enter', ' ']
  if (!handled.includes(event.key)) return
  event.preventDefault(); event.stopPropagation()
  if (event.key === 'ArrowDown') void focusRow(index + 1)
  if (event.key === 'ArrowUp') void focusRow(index - 1)
  if (event.key === 'Home') void focusRow(0)
  if (event.key === 'End') void focusRow(rows.value.length - 1)
  if (event.key === 'Enter' || event.key === ' ') { if (row.kind === 'employee') choose(row.id, true) }
  if (row.kind === 'pager') {
    if (event.key === 'ArrowLeft' && (props.pages.get(row.id) ?? 0) > 0) emit('page', row.id, -1)
    if (event.key === 'ArrowRight' && ((props.pages.get(row.id) ?? 0) + 1) * props.pageSize < props.org.children.get(row.id)!.length) emit('page', row.id, 1)
    return
  }
  if (event.key === 'ArrowRight' && props.org.children.get(row.id)!.length) { if (!props.expanded.has(row.id)) emit('toggle', row.id); else void focusRow(index + 1) }
  if (event.key === 'ArrowLeft') {
    if (props.expanded.has(row.id)) emit('toggle', row.id)
    else { const parent = props.org.employees.get(row.id)!.managerId; if (parent) void focusRow(rows.value.findIndex(value => value.id === parent)) }
  }
}
onMounted(() => {
  observer = new ResizeObserver(([entry]) => {
    const wasHidden = containerHeight.value <= 0
    containerHeight.value = entry.contentRect.height
    if (wasHidden && entry.contentRect.height > 0) void revealSelected()
  })
  observer.observe(container.value!); void revealSelected()
})
onBeforeUnmount(() => observer?.disconnect())
</script>
<template>
  <div class="hierarchy-navigator">
    <div class="panel-heading"><h2>Hierarchy</h2><button class="icon-button" aria-label="Close hierarchy navigator" @click="$emit('close')">×</button></div>
    <div class="navigator-search"><label :for="searchId" class="sr-only">Search employees by name or ID</label><input :id="searchId" v-model="query" type="search" placeholder="Search name or ID" @keydown.escape="query = ''"><span class="navigator-search-hint">{{ org.employees.size.toLocaleString() }} people · names may repeat</span></div>
    <div v-if="query.trim()" class="navigator-results"><p class="navigator-caption">{{ matches.length ? 'Up to 30 results' : 'No employees found' }}</p><button v-for="match in matches" :key="match.id" class="search-result" :aria-label="`Find ${match.name} (${match.id})`" @click="choose(match.id, $event.detail === 0)"><span>{{ match.name }}</span><small>{{ match.id }} · {{ match.title || 'Employee' }}</small></button></div>
    <div v-show="!query.trim()" ref="container" class="navigator-tree" role="tree" aria-label="Reporting hierarchy" @scroll="scroll = ($event.target as HTMLElement).scrollTop">
      <div :style="{ height: `${rows.length * rowHeight}px`, position: 'relative' }"><div v-for="(row, offset) in virtualRows" :key="row.key" class="navigator-row" :class="{ 'nav-selected': row.kind === 'employee' && selected === row.id }" :style="{ top: `${(start + offset) * rowHeight}px`, paddingLeft: `${10 + Math.min(row.depth, 8) * 12}px` }" role="treeitem" :aria-description="row.kind === 'employee' ? `Employee ID ${row.id}, level ${row.depth}` : `Report pages for ${row.id}. Left and right arrows change page.`" :aria-level="row.depth + 1" :aria-selected="row.kind === 'employee' ? selected === row.id : undefined" :aria-expanded="row.kind === 'employee' && org.children.get(row.id)!.length ? expanded.has(row.id) : undefined" :aria-posinset="row.kind === 'employee' ? row.position : undefined" :aria-setsize="row.kind === 'employee' ? row.siblings : undefined" :tabindex="active === row.key || (!activeVisible && offset === 0) ? 0 : -1" :data-nav-row="row.kind === 'employee' ? row.id : row.key" :data-nav-key="row.key" @keydown="key($event, row)" @focus="active = row.key" @click="row.kind === 'employee' && choose(row.id)">
        <template v-if="row.kind === 'employee'"><button v-if="org.children.get(row.id)!.length" class="nav-chevron" tabindex="-1" :aria-label="`${expanded.has(row.id) ? 'Collapse' : 'Expand'} navigator ${row.id}`" @click.stop="$emit('toggle', row.id)">{{ expanded.has(row.id) ? '⌄' : '›' }}</button><span v-else class="nav-leaf" aria-hidden="true">·</span><span class="nav-employee"><span :title="org.employees.get(row.id)!.name">{{ org.employees.get(row.id)!.name }}</span><small :title="org.employees.get(row.id)!.title">{{ org.employees.get(row.id)!.title || row.id }}</small></span><span v-if="org.children.get(row.id)!.length" class="nav-report-count">{{ org.children.get(row.id)!.length }}</span></template>
        <template v-else><div class="nav-pagination"><button tabindex="-1" :disabled="!(pages.get(row.id) ?? 0)" :aria-label="`Previous navigator reports for ${row.id}`" @click.stop="$emit('page', row.id, -1)">‹</button><span>{{ (pages.get(row.id) ?? 0) + 1 }} / {{ Math.ceil(org.children.get(row.id)!.length / pageSize) }}</span><button tabindex="-1" :disabled="((pages.get(row.id) ?? 0) + 1) * props.pageSize >= org.children.get(row.id)!.length" :aria-label="`Next navigator reports for ${row.id}`" @click.stop="$emit('page', row.id, 1)">›</button></div></template>
      </div></div>
    </div>
    <div class="navigator-footer">Select a person to focus their team.<br>Arrow keys navigate; Enter selects.</div>
  </div>
</template>
