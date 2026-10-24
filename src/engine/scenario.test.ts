import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { buildOrganization, loadOrganization, type Employee, type Organization } from './organization'
import { simulateMove, validateMove } from './scenario'
const employee = (id: string, managerId: string | null, salaryMinor = 100): Employee => ({ id, managerId, name: id, salaryMinor })
const fixture = () => buildOrganization([employee('root', null, 900), employee('a', 'root', 200), employee('b', 'root', 300), employee('c', 'a', 400), employee('d', 'c', 500)])
function reconcile(baseline: Organization, moving: string, destination: string) {
  const scenario = simulateMove(baseline, moving, destination)
  const rebuilt = buildOrganization([...baseline.employees.values()].map(e => e.id === moving ? { ...e, managerId: destination } : e))
  expect(scenario.organization.metrics).toEqual(rebuilt.metrics)
  const membership = (org: Organization) => new Map([...org.children].map(([id, reports]) => [id, [...reports].sort()]))
  expect(membership(scenario.organization)).toEqual(membership(rebuilt))
  expect(scenario.organization.roots).toEqual(rebuilt.roots)
  return scenario
}
describe('scenario moves', () => {
  it('rejects self moves, descendants, existing reporting relationships, and missing IDs', () => {
    const org = fixture()
    expect(validateMove(org, 'a', 'a')).toContain('themselves')
    expect(validateMove(org, 'a', 'd')).toContain('descendants')
    expect(validateMove(org, 'a', 'root')).toContain('already')
    expect(() => simulateMove(org, 'missing', 'root')).toThrow('existing employee')
    expect(() => simulateMove(org, 'a', 'missing')).toThrow('destination')
  })
  it('moves a manager and team while accounting for destination promotion and source demotion', () => {
    const org = fixture(), original = JSON.stringify([...org.metrics])
    const s = reconcile(org, 'c', 'b')
    expect(s.organization.children.get('a')).toEqual([])
    expect(s.organization.children.get('b')).toEqual(['c'])
    expect(s.organization.metrics.get('root')!.managementCostMinor - org.metrics.get('root')!.managementCostMinor).toBe(100)
    expect(s.organization.metrics.get('root')!.totalCostMinor).toBe(org.metrics.get('root')!.totalCostMinor)
    expect(s.organization.metrics.get('c')).toBe(org.metrics.get('c'))
    expect(JSON.stringify([...org.metrics])).toBe(original)
    expect(org.children.get('a')).toEqual(['c']); expect(org.children.get('b')).toEqual([])
    expect(org.employees.get('c')!.managerId).toBe('a')
  })
  it('supports moving an IC to an ancestor and moving a root across a forest', () => {
    reconcile(fixture(), 'd', 'root')
    const forest = buildOrganization([employee('a', null), employee('b', null), employee('c', 'a')])
    const s = reconcile(forest, 'a', 'b')
    expect(s.organization.roots).toEqual(['b'])
    expect(forest.roots).toEqual(['a', 'b'])
  })
  it('matches a complete rebuild for deterministic varied valid moves', () => {
    const org = buildOrganization(Array.from({ length: 150 }, (_, i) => employee(String(i), i ? String(Math.floor((i - 1) / 3)) : null, i * 101)))
    for (let i = 1; i < 150; i++) {
      const destination = String((i * 37 + 11) % 150)
      if (!validateMove(org, String(i), destination)) reconcile(org, String(i), destination)
    }
  })
  it('handles deep paths iteratively and rejects unsafe merged totals', () => {
    const deep = buildOrganization(Array.from({ length: 40000 }, (_, i) => employee(String(i), i ? String(i - 1) : null, 1)))
    const s = simulateMove(deep, '39999', '0')
    expect(s.organization.metrics.get('0')!.descendantCount).toBe(39999)
    expect(s.organization.metrics.get('39998')!.descendantCount).toBe(0)
    expect(validateMove(deep, '0', '39999')).toContain('descendants')
    expect(() => buildOrganization([employee('a', null), employee('b', 'a', Number.MAX_SAFE_INTEGER), employee('c', null, 1)])).toThrow('precision')
  })
  it('reconciles a 40k team move and leaves the baseline untouched', () => {
    const org = loadOrganization(readFileSync(new URL('../../data/giga-corp-synthetic-40000.csv', import.meta.url), 'utf8'))
    const before = org.metrics.get('GC000001')!.totalCostMinor
    reconcile(org, 'GC000002', 'GC000007')
    expect(org.employees.get('GC000002')!.managerId).toBe('GC000001')
    expect(org.metrics.get('GC000001')!.totalCostMinor).toBe(before)
  })
})
