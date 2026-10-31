import { describe, expect, it } from 'vitest'
import { buildOrganization, loadOrganization } from './organization'
import { navigatorRows } from './navigator'

describe('QA input and navigation regressions', () => {
  it('preserves exact decimal cents near the safe integer boundary', () => {
    const org = loadOrganization('Employee Id,Manager,Name,Salary\nr,,Root,90071992547409.90')
    expect(org.employees.get('r')!.salaryMinor).toBe(9007199254740990)
  })
  it('rejects a global salary total that analytics cannot represent safely', () => {
    expect(() => buildOrganization([
      { id: 'r', name: 'Root', managerId: null, salaryMinor: Number.MAX_SAFE_INTEGER },
      { id: 'c', name: 'Child', managerId: 'r', salaryMinor: 100 },
    ])).toThrow('precision')
  })
  it('rejects duplicate CSV columns instead of silently selecting an ambiguous one', () => {
    expect(() => loadOrganization('Employee Id,Manager,Name,Salary,Salary\nr,,Root,100,200')).toThrow('Duplicate CSV column')
  })
  it('gives pager rows and arbitrary employee IDs different stable keys', () => {
    const employees = [{ id: 'r', name: 'Root', managerId: null, salaryMinor: 1 },
      ...Array.from({ length: 5 }, (_, i) => ({ id: i ? String(i) : 'pager-r', name: 'Duplicate Name', managerId: 'r', salaryMinor: 1 }))]
    const rows = navigatorRows(buildOrganization(employees), new Set(['r']), new Map(), 4)
    expect(new Set(rows.map(row => row.key)).size).toBe(rows.length)
  })
})
