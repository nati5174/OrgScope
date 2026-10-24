import { computed, nextTick, ref, shallowRef } from 'vue'
import type { Organization } from '../engine/organization'
import { ancestorPath, visibleNodes, NODE_LIMIT } from '../engine/explorer'
import { revealInNavigator } from '../engine/navigator'

export function useExplorer(org: Organization) {
  const selected = ref(org.roots[0]), focus = ref(org.roots[0])
  const expanded = shallowRef(new Set([focus.value])), pages = shallowRef(new Map<string, number>())
  const pageSize = ref(4)
  const renderMs = ref<number | null>(null)
  const nodes = computed(() => visibleNodes(org, focus.value, expanded.value, pages.value, NODE_LIMIT, pageSize.value))
  const path = computed(() => ancestorPath(org, focus.value))
  function reveal(id: string) {
    const state = revealInNavigator(org, id, expanded.value, pages.value, pageSize.value)
    // Keep the original references when merely selecting an already revealed row.
    if (state.expanded.size !== expanded.value.size) expanded.value = state.expanded
    if ([...state.pages].some(([key, value]) => (pages.value.get(key) ?? 0) !== value)) pages.value = state.pages
  }
  function select(id: string) { selected.value = id; reveal(id) }
  function focusTeam(id: string) {
    select(id); focus.value = id
    if (!expanded.value.has(id)) expanded.value = new Set([...expanded.value, id])
  }
  async function toggle(id: string) {
    const start = performance.now(), next = new Set(expanded.value)
    if (next.has(id)) {
      next.delete(id)
      // If the selection becomes hidden, select the collapsed manager so panes agree.
      if (ancestorPath(org, selected.value).slice(0, -1).includes(id)) selected.value = id
      if (ancestorPath(org, focus.value).slice(0, -1).includes(id)) focus.value = id
    } else next.add(id)
    expanded.value = next
    await nextTick(); renderMs.value = performance.now() - start
  }
  function page(id: string, delta: number) {
    const next = new Map(pages.value); next.set(id, (next.get(id) ?? 0) + delta); pages.value = next
    const selectedPath = ancestorPath(org, selected.value), child = selectedPath[selectedPath.indexOf(id) + 1]
    if (selectedPath.includes(id) && child && !org.children.get(id)?.slice(next.get(id)! * pageSize.value, next.get(id)! * pageSize.value + pageSize.value).includes(child)) {
      selected.value = id
      if (ancestorPath(org, focus.value).slice(0, -1).includes(id)) focus.value = id
    }
  }
  function collapseAll() {
    const ancestors = revealInNavigator(org, focus.value, new Set(), pages.value, pageSize.value)
    expanded.value = ancestors.expanded; selected.value = focus.value
  }
  function setPageSize(value: number) { pageSize.value = value; pages.value = new Map(); reveal(selected.value) }
  return { selected, focus, expanded, pages, pageSize, nodes, path, renderMs, select, focusTeam, toggle, page, collapseAll, setPageSize }
}
