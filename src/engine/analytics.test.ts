import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { buildOrganization, loadOrganization, type Employee } from './organization'
import { analyzeWorkforce } from './analytics'
const employee = (id: string, managerId: string | null, salaryMinor: number): Employee => ({ id, managerId, name: id, salaryMinor })
const org = buildOrganization([employee('a', null, 900), employee('b', 'a', 200), employee('c', 'b', 300), employee('d', 'a', 400)])
describe('workforce analytics', () => {
  it('includes the selected leader, reconciles branches and classifies managers', () => {
    const result = analyzeWorkforce(org, 'a')
    expect(result.headcount).toBe(4); expect(result.managers).toBe(2); expect(result.ics).toBe(2)
    expect(result.totalCostMinor).toBe(1800); expect(result.managementCostMinor).toBe(1100); expect(result.icCostMinor).toBe(700)
    expect(result.averageSalaryMinor).toBe(450); expect(result.averageSpan).toBe(1.5)
    expect(result.maxDepth).toBe(2); expect(result.managementLayers).toBe(2)
    expect(result.branches.map(b => b.id)).toEqual(['b', 'd'])
    expect(result.branches.reduce((sum, b) => sum + b.totalCostMinor, result.leaderCostMinor)).toBe(result.totalCostMinor)
    expect(result.depthBuckets.map(b => b.count)).toEqual([1, 2, 1])
  })
  it('scopes costs and depth to a subtree and supports IC and zero-salary cases', () => {
    const result = analyzeWorkforce(org, 'b')
    expect(result.headcount).toBe(2); expect(result.totalCostMinor).toBe(500); expect(result.maxDepth).toBe(1)
    const leaf = analyzeWorkforce(org, 'c')
    expect(leaf.branches).toHaveLength(0); expect(leaf.managementCostMinor).toBe(0); expect(leaf.averageSpan).toBeNull()
    const zero = analyzeWorkforce(buildOrganization([employee('zero', null, 0)]), null)
    expect(zero.salaryBuckets).toEqual([{ label: 'Salary band 1', minMinor: 0, maxMinor: 0, count: 1 }])
    expect(zero.totalCostMinor).toBe(0)
  })
  it('supports forests without counting a leader twice', () => {
    const forest = buildOrganization([employee('a', null, 100), employee('b', null, 200), employee('c', 'b', 300)])
    const result = analyzeWorkforce(forest, null)
    expect(result.headcount).toBe(3); expect(result.totalCostMinor).toBe(600)
    expect(result.leaderCostMinor).toBe(0); expect(result.branches.map(b => b.id)).toEqual(['b', 'a'])
    expect(result.branches.reduce((sum, b) => sum + b.totalCostMinor, 0)).toBe(600)
    expect(() => analyzeWorkforce(forest, 'missing')).toThrow('Unknown analytics scope')
  })
  it('handles small cent ranges and equal salaries without dropping histogram records', () => {
    for (const values of [[100, 100, 100], [100, 101, 102], [0, 1, 90000]]) {
      const result = analyzeWorkforce(buildOrganization(values.map((salary, i) => employee(String(i), i ? '0' : null, salary))), null)
      expect(result.salaryBuckets.reduce((sum, b) => sum + b.count, 0)).toBe(values.length)
      for (const value of values) expect(result.salaryBuckets.filter(b => value >= b.minMinor && value <= b.maxMinor)).toHaveLength(1)
    }
  })
  it('handles a 40k-level chain without stack overflow and groups deep layers', () => {
    const deep = buildOrganization(Array.from({ length: 40000 }, (_, i) => employee(String(i), i ? String(i - 1) : null, 1)))
    const result = analyzeWorkforce(deep, null)
    expect(result.maxDepth).toBe(39999); expect(result.managementLayers).toBe(39999)
    expect(result.depthBuckets).toHaveLength(11); expect(result.depthBuckets[10].count).toBe(39990)
  })
  it('reconciles distributions, branch totals, and supplied salaries for 40k employees', () => {
    const data = loadOrganization(readFileSync(new URL('../../data data.csv', import.meta.url), 'utf8'))
    const result = analyzeWorkforce(data, null)
    expect(result.headcount).toBe(40000)
    expect(result.totalCostMinor).toBe([...data.employees.values()].reduce((sum, e) => sum + e.salaryMinor, 0))
    expect(result.totalCostMinor).toBe(result.managementCostMinor + result.icCostMinor)
    expect(result.salaryBuckets.reduce((sum, b) => sum + b.count, 0)).toBe(result.headcount)
    expect(result.depthBuckets.reduce((sum, b) => sum + b.count, 0)).toBe(result.headcount)
    expect(result.spanBuckets.reduce((sum, b) => sum + b.count, 0)).toBe(result.managers)
    expect(result.branches.reduce((sum, b) => sum + b.totalCostMinor, result.leaderCostMinor)).toBe(result.totalCostMinor)
    expect(result.branches.reduce((sum, b) => sum + b.headcount, 1)).toBe(result.headcount)
  })
})
