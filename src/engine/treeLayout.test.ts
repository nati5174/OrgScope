import { describe, expect, it } from 'vitest'
import { buildOrganization, type Employee } from './organization'
import { visibleNodes } from './explorer'
import { CARD_HEIGHT, CARD_WIDTH, layoutTree } from './treeLayout'
import { navigatorRows, revealInNavigator } from './navigator'
const employee = (id: string, managerId: string | null): Employee => ({ id, managerId, name: id, salaryMinor: 100 })
const org = buildOrganization([employee('root', null), ...Array.from({ length: 24 }, (_, i) => employee(String(i), 'root')),
  ...Array.from({ length: 24 }, (_, i) => employee(`child-${i}`, '0'))])
describe('tidy tree layout and navigator', () => {
  it('keeps cards disjoint and connector segments outside card interiors', () => {
    const nodes = visibleNodes(org, 'root', new Set(['root', '0']), new Map())
    const layout = layoutTree(nodes)
    for (let i = 0; i < layout.nodes.length; i++) {
      const a = layout.nodes[i]
      for (const b of layout.nodes.slice(i + 1)) {
        expect(a.x + CARD_WIDTH <= b.x || b.x + CARD_WIDTH <= a.x || a.y + CARD_HEIGHT <= b.y || b.y + CARD_HEIGHT <= a.y).toBe(true)
      }
    }
    for (const connector of layout.connectors) {
      for (const [x1, y1, x2, y2] of connector.segments) {
        for (const node of layout.nodes) {
          const minX = Math.min(x1, x2), maxX = Math.max(x1, x2), minY = Math.min(y1, y2), maxY = Math.max(y1, y2)
          const crosses = x1 === x2
            ? x1 > node.x && x1 < node.x + CARD_WIDTH && maxY > node.y && minY < node.y + CARD_HEIGHT
            : y1 > node.y && y1 < node.y + CARD_HEIGHT && maxX > node.x && minX < node.x + CARD_WIDTH
          expect(crosses).toBe(false)
        }
      }
    }
  })
  it('compacts after collapse and centers parents over their children', () => {
    const base = layoutTree(visibleNodes(org, 'root', new Set(['root']), new Map()))
    const expanded = layoutTree(visibleNodes(org, 'root', new Set(['root', '0']), new Map()))
    expect(expanded.height).toBeGreaterThan(base.height)
    expect(expanded.width).toBeGreaterThan(base.width)
    const root = base.nodes.find(n => n.id === 'root')!, children = base.nodes.filter(n => n.parentId === 'root')
    expect(root.y).toBe((children[0].y + children.at(-1)!.y) / 2)
    expect(layoutTree(visibleNodes(org, 'root', new Set(['root']), new Map()))).toEqual(base)
  })
  it('reveals a paginated path while preserving unrelated expansions', () => {
    const state = revealInNavigator(org, '23', new Set(['0']), new Map([['0', 1]]))
    expect(state.expanded.has('0')).toBe(true); expect(state.pages.get('0')).toBe(1)
    expect(state.pages.get('root')).toBe(2)
    const rows = navigatorRows(org, state.expanded, state.pages)
    expect(rows.some(row => row.id === '23')).toBe(true)
    expect(rows.some(row => row.kind === 'pager')).toBe(true)
  })
  it('flattens 40k-level paths without recursive stack overflow', () => {
    const deep = buildOrganization(Array.from({ length: 40000 }, (_, i) => employee(String(i), i ? String(i - 1) : null)))
    const state = revealInNavigator(deep, '39999', new Set(), new Map())
    const rows = navigatorRows(deep, state.expanded, state.pages)
    expect(rows).toHaveLength(40000); expect(rows.at(-1)!.id).toBe('39999')
  })
})
