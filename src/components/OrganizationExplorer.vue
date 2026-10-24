<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'
import type { Organization } from '../engine/organization'
import { NODE_LIMIT } from '../engine/explorer'
import { useExplorer } from '../composables/useExplorer'
import OrgCanvas from './OrgCanvas.vue'
import HierarchyNavigator from './HierarchyNavigator.vue'
import EmployeeDetails from './EmployeeDetails.vue'
import ExplorerPanel from './ExplorerPanel.vue'
const props = defineProps<{ org: Organization; requestedEmployee?: string | null; hideAnalysis?: boolean }>()
const emit = defineEmits<{ analyze: [id: string] }>()
const { selected, focus, expanded, pages, pageSize, nodes, path, renderMs, select, focusTeam, toggle, page, collapseAll, setPageSize } = useExplorer(props.org)
const desktop = ref(window.matchMedia('(min-width: 1280px)').matches)
const navOpen = ref(desktop.value), inspectorOpen = ref(desktop.value), canvas = ref<InstanceType<typeof OrgCanvas>>()
const statusId = useId(), rootSelectId = useId(), densityId = useId()
const crumbs = computed(() => path.value.length > 4 ? [path.value[0], ...path.value.slice(-3)] : path.value)
const selectedDepth = computed(() => {
  let depth = 0, employee = props.org.employees.get(selected.value)!
  while (employee.managerId) { depth++; employee = props.org.employees.get(employee.managerId)! }
  return depth
})
function chooseCard(id: string) { select(id); if (!desktop.value) inspectorOpen.value = true }
function toggleNode(id: string) { canvas.value?.anchorOn(id); void toggle(id) }
function pageReports(id: string, delta: number) { canvas.value?.anchorOn(id); page(id, delta) }
async function changeDensity(value: number) { setPageSize(value); await nextTick(); canvas.value?.fit() }
function analyzeEmployee(id: string) { if (!desktop.value) inspectorOpen.value = false; emit('analyze', id) }
async function focusHere(id: string) {
  focusTeam(id)
  if (!desktop.value) { navOpen.value = false; inspectorOpen.value = false }
  await nextTick(); if (desktop.value) canvas.value?.frameInitial(); else canvas.value?.reset()
}
function home() {
  const root = props.org.roots[0]
  if (pages.value.get(root)) { const next = new Map(pages.value); next.set(root, 0); pages.value = next }
  focusHere(root)
}
function back() { const parent = props.org.employees.get(focus.value)!.managerId; if (parent) focusHere(parent) }
let media: MediaQueryList | undefined
function resize(event: MediaQueryListEvent) { desktop.value = event.matches; navOpen.value = event.matches; inspectorOpen.value = event.matches }
onMounted(() => { media = window.matchMedia('(min-width: 1280px)'); media.addEventListener('change', resize) })
onBeforeUnmount(() => media?.removeEventListener('change', resize))
watch(() => props.requestedEmployee, id => { if (id) void focusHere(id) }, { immediate: true })
</script>
<template>
  <section class="explorer" aria-label="Organization explorer">
    <div class="explorer-heading"><div><p class="eyebrow">Organization explorer</p><h1>A clearer view of your people.</h1></div><div class="explorer-heading-meta"><span class="legend-dot"></span>{{ org.employees.size.toLocaleString() }} people <span class="text-slate-300">/</span> {{ org.roots.length === 1 ? 'One organization' : `${org.roots.length} roots` }}</div></div>
    <div class="explorer-workspace" :class="{ 'has-navigator': desktop && navOpen, 'has-inspector': desktop && inspectorOpen }">
      <ExplorerPanel :open="navOpen" :desktop="desktop" side="left" label="Hierarchy navigator" @close="navOpen = false"><HierarchyNavigator :org="org" :selected="selected" :expanded="expanded" :pages="pages" :page-size="pageSize" @select="focusHere" @toggle="toggleNode" @page="pageReports" @close="navOpen = false" /></ExplorerPanel>
      <div class="chart-workspace">
        <div class="workspace-context"><nav aria-label="Reporting breadcrumbs"><button class="breadcrumb-home" @click="home">Organization</button><template v-for="(id, index) in crumbs" :key="id"><span aria-hidden="true">{{ index === 1 && path.length > 4 ? '…' : '/' }}</span><button :title="`${org.employees.get(id)!.name} (${id})`" :aria-current="id === focus ? 'location' : undefined" @click="focusHere(id)">{{ org.employees.get(id)!.name }}</button></template></nav><button class="context-back" :disabled="!org.employees.get(focus)!.managerId" @click="back">↑ Up one level</button></div>
        <div class="workspace-actions"><div class="flex items-center gap-2"><button class="toolbar" :aria-expanded="navOpen" @click="navOpen = !navOpen">☰ Hierarchy</button><button class="toolbar" :aria-expanded="inspectorOpen" @click="inspectorOpen = !inspectorOpen">Inspector</button></div><div class="flex items-center gap-2"><button class="toolbar" @click="focusHere(selected)">Focus on Team</button><button class="toolbar" @click="collapseAll">Collapse all</button></div></div>
        <div class="density-control"><label :for="densityId">Reports per page</label><select :id="densityId" :value="pageSize" @change="changeDensity(Number(($event.target as HTMLSelectElement).value))"><option :value="4">4 · compact</option><option :value="8">8 · standard</option><option :value="24">24 · wide team</option></select><span>Choose a team to explore its reports</span></div>
        <div v-if="org.roots.length > 1" class="root-selector"><label :for="rootSelectId">Organization root</label><select :id="rootSelectId" :value="path[0]" @change="focusHere(($event.target as HTMLSelectElement).value)"><option v-for="id in org.roots" :key="id" :value="id">{{ org.employees.get(id)!.name }} · {{ id }}</option></select></div>
        <OrgCanvas ref="canvas" :org="org" :nodes="nodes" :selected="selected" :focus-id="focus" :expanded="expanded" :pages="pages" :page-size="pageSize" @select="chooseCard" @toggle="toggleNode" @page="pageReports" @focus="focusHere" />
        <div :id="statusId" role="status" class="workspace-status"><span>{{ nodes.length >= NODE_LIMIT ? '150-card limit reached. Focus on a team or collapse a branch to explore further.' : 'Select to inspect · Focus to explore a team · Drag to pan' }}</span><span v-if="renderMs !== null">Last update {{ renderMs.toFixed(1) }} ms · paint excluded</span></div>
      </div>
      <ExplorerPanel :open="inspectorOpen" :desktop="desktop" side="right" label="Employee inspector" @close="inspectorOpen = false"><EmployeeDetails :org="org" :id="selected" :depth="selectedDepth" :hide-analysis="hideAnalysis" @focus="focusHere" @select="focusHere" @analyze="analyzeEmployee" @close="inspectorOpen = false" /></ExplorerPanel>
    </div>
  </section>
</template>
