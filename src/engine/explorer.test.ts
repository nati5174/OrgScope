import { describe, expect, it } from 'vitest'
import { buildOrganization, loadOrganization, type Employee } from './organization'
import { ancestorPath, visibleNodes, revealEmployee, NODE_LIMIT, PAGE_SIZE } from './explorer'
import { readFileSync } from 'node:fs'
const employee = (id: string, managerId: string | null): Employee => ({ id, managerId, name: id, salaryMinor: 100 })
describe('bounded explorer', () => {
  it('expands, collapses, and pages wide reporting groups', () => {
    const org = buildOrganization([employee('root', null), ...Array.from({ length: 100 }, (_, i) => employee(String(i), 'root'))])
    expect(visibleNodes(org, 'root', new Set(), new Map())).toHaveLength(1)
    expect(visibleNodes(org, 'root', new Set(['root']), new Map())).toHaveLength(PAGE_SIZE + 1)
    const page = visibleNodes(org, 'root', new Set(['root']), new Map([['root', 12]]))
    expect(page.map(n => n.id)).toEqual(['root', '96', '97', '98', '99'])
    const reveal = revealEmployee(org, '99')
    expect(visibleNodes(org, reveal.focus, reveal.expanded, reveal.pages).some(n => n.id === '99')).toBe(true)
  })
  it('bounds rendering and reveals a deep employee without rendering their full ancestor chain', () => {
    const org = buildOrganization(Array.from({ length: 40000 }, (_, i) => employee(String(i), i ? String(i - 1) : null)))
    const expanded = new Set(org.employees.keys())
    expect(visibleNodes(org, '0', expanded, new Map())).toHaveLength(NODE_LIMIT)
    expect(ancestorPath(org, '39999')).toHaveLength(40000)
    const reveal = revealEmployee(org, '39999')
    expect(reveal.focus).toBe('39998')
    expect(visibleNodes(org, reveal.focus, reveal.expanded, reveal.pages).map(n => n.id)).toEqual(['39998', '39999'])
  })
  it('keeps all visible children attached to a visible parent in the 40k dataset', () => {
    const org = loadOrganization(readFileSync(new URL('../../data/giga-corp-synthetic-40000.csv', import.meta.url), 'utf8'))
    const nodes = visibleNodes(org, org.roots[0], new Set(org.employees.keys()), new Map())
    const ids = new Set(nodes.map(n => n.id))
    expect(nodes.length).toBe(NODE_LIMIT)
    for (const node of nodes) if (node.parentId) expect(ids.has(node.parentId)).toBe(true)
  })
})
