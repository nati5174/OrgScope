import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { buildOrganization, loadOrganization, managementCostRatio, searchEmployees, type Employee } from './organization'
const person = (id: string, managerId: string | null, salaryMinor = 100): Employee => ({ id, managerId, name: `Person ${id}`, salaryMinor })
const csv = 'employee_id,manager_id,name,salary,currency\n'

describe('hierarchy engine', () => {
  it('excludes a solitary employee from descendant metrics', () => {
    const org = buildOrganization([person('1', null)])
    expect(org.metrics.get('1')).toEqual({ descendantCount: 0, nonLeafDescendantCount: 0, managementCostMinor: 0, icCostMinor: 0, totalCostMinor: 0 })
    expect(managementCostRatio(org.metrics.get('1')!)).toBeNull()
  })
  it('aggregates multiple levels independent of row order and reconciles costs', () => {
    const org = buildOrganization([person('c', 'b', 300), person('a', null, 900), person('d', 'a', 400), person('b', 'a', 200)])
    expect(org.metrics.get('a')).toEqual({ descendantCount: 3, nonLeafDescendantCount: 1, managementCostMinor: 200, icCostMinor: 700, totalCostMinor: 900 })
    expect(org.metrics.get('b')?.totalCostMinor).toBe(300)
    expect(managementCostRatio(org.metrics.get('a')!)).toBe(3.5)
    expect(searchEmployees(org, 'PERSON C')[0].id).toBe('c')
    expect(searchEmployees(org, 'person', 2)).toHaveLength(2)
  })
  it('supports multiple roots', () => expect(buildOrganization([person('a', null), person('b', null)]).roots).toHaveLength(2))
  it('rejects missing managers and duplicate IDs', () => {
    expect(() => buildOrganization([person('a', 'missing')])).toThrow('Missing manager')
    expect(() => buildOrganization([person('a', null), person('a', null)])).toThrow('Duplicate')
  })
  it('detects self cycles and disconnected cyclic components', () => {
    expect(() => buildOrganization([person('a', 'a')])).toThrow('Cyclic')
    expect(() => buildOrganization([person('root', null), person('a', 'b'), person('b', 'a')])).toThrow('Cyclic')
  })
  it('handles a 40,000-level chain without recursive stack overflow', () => {
    const org = buildOrganization(Array.from({ length: 40000 }, (_, i) => person(String(i), i ? String(i - 1) : null)))
    expect(org.metrics.get('0')?.descendantCount).toBe(39999)
    expect(org.metrics.get('0')?.nonLeafDescendantCount).toBe(39998)
    expect(org.metrics.get('0')?.totalCostMinor).toBe(3999900)
  })
  it('parses BOM, quoted names, embedded newlines, blank lines, and zero-padded IDs', () => {
    const org = loadOrganization('\uFEFF' + csv + '001,,"Chen, Alex\nJr",100.25,CAD\n\n002,001,Sam,0,CAD')
    expect(org.employees.get('001')?.name).toBe('Chen, Alex\nJr')
    expect(org.employees.get('001')?.salaryMinor).toBe(10025)
    expect(org.metrics.get('001')?.descendantCount).toBe(1)
  })
  it.each(['-1', 'NaN', '', '1.234', '1,000', 'Infinity'])('rejects invalid salary %s', salary => {
    expect(() => loadOrganization(csv + `1,,Alex,"${salary}",CAD`)).toThrow('salary')
  })
  it('rejects missing headers, malformed CSV, empty data, mixed currencies, unsafe totals', () => {
    expect(() => loadOrganization('name\nAlex')).toThrow('Missing required column')
    expect(() => loadOrganization(csv + '1,,"Alex,10,CAD')).toThrow('CSV row')
    expect(() => loadOrganization(csv)).toThrow('no employees')
    expect(() => loadOrganization(csv + '1,,Alex,1,CAD\n2,1,Sam,2,USD')).toThrow('Mixed currencies')
    expect(() => buildOrganization([person('a', null), person('b', 'a', Number.MAX_SAFE_INTEGER), person('c', 'a')])).toThrow('precision')
  })
  it('reconciles the generated 40k dataset against its independent summary', () => {
    const org = loadOrganization(readFileSync(new URL('../../data/giga-corp-synthetic-40000.csv', import.meta.url), 'utf8'))
    const summary = JSON.parse(readFileSync(new URL('../../data/synthetic-summary.json', import.meta.url), 'utf8'))
    expect(org.employees.size).toBe(40000)
    const root = org.metrics.get(org.roots[0])!
    expect(root.descendantCount).toBe(summary.ceo_descendant_count)
    expect(root.nonLeafDescendantCount).toBe(summary.ceo_non_leaf_descendant_count)
    expect(root.managementCostMinor).toBe(summary.ceo_descendant_management_cost * 100)
    expect(root.icCostMinor).toBe(summary.ceo_descendant_ic_cost * 100)
    expect(root.totalCostMinor).toBe(summary.ceo_descendant_total_cost * 100)
    for (const m of org.metrics.values()) expect(m.totalCostMinor).toBe(m.managementCostMinor + m.icCostMinor)
  })
})
