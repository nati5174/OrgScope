import { describe, expect, it } from 'vitest'
import { buildOrganization, type Employee } from '../engine/organization'
import { useExplorer } from './useExplorer'
const employee = (id: string, managerId: string | null): Employee => ({ id, managerId, name: id, salaryMinor: 100 })
const org = buildOrganization([employee('root', null), ...Array.from({ length: 24 }, (_, i) => employee(String(i), 'root')),
  employee('deep', '0'), employee('leaf', 'deep')])
describe('synchronized explorer state', () => {
  it('does not recalculate the chart projection when selecting a revealed employee', () => {
    const state = useExplorer(org), nodes = state.nodes.value
    state.select('1')
    expect(state.selected.value).toBe('1'); expect(state.nodes.value).toBe(nodes)
    expect(state.focus.value).toBe('root')
  })
  it('preserves unrelated expansion and reveals ancestors when focusing an employee', async () => {
    const state = useExplorer(org)
    await state.toggle('1'); state.focusTeam('leaf')
    expect(state.expanded.value.has('1')).toBe(true)
    expect(state.expanded.value.has('0')).toBe(true)
    expect(state.expanded.value.has('deep')).toBe(true)
    expect(state.path.value).toEqual(['root', '0', 'deep', 'leaf'])
    expect(state.selected.value).toBe('leaf'); expect(state.focus.value).toBe('leaf')
    await state.toggle('0')
    expect(state.focus.value).toBe('0'); expect(state.selected.value).toBe('0')
  })
  it('keeps selection visible when paging, changing density, or collapsing', () => {
    const state = useExplorer(org)
    state.focusTeam('leaf'); state.page('root', 1)
    expect(state.selected.value).toBe('root'); expect(state.focus.value).toBe('root')
    state.focusTeam('23'); expect(state.pages.value.get('root')).toBe(5)
    state.setPageSize(8); expect(state.pages.value.get('root')).toBe(2)
    state.collapseAll(); expect(state.selected.value).toBe('23')
    expect(state.expanded.value.has('root')).toBe(true); expect(state.expanded.value.has('23')).toBe(false)
  })
})
