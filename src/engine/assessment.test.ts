import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { loadOrganization } from './organization'

describe('supplied assessment data', () => {
  it('loads every employee and reconciles salary totals with an independent Decimal sum', () => {
    const org = loadOrganization(readFileSync(new URL('../../data data.csv', import.meta.url), 'utf8'))
    expect(org.employees.size).toBe(40000)
    expect(org.roots).toEqual(['p_DrnEHzsrxaHOPnwwNDBwy'])
    expect(org.currency).toBe('XXX')
    const root = org.employees.get(org.roots[0])!
    expect(root.name).toBe('Melody Himes')
    expect(root.title).toBe('CEO')
    expect(root.location).toBe('Toronto, Canada')
    const metrics = org.metrics.get(root.id)!
    expect(metrics.descendantCount).toBe(39999)
    expect(metrics.totalCostMinor + root.salaryMinor).toBe(242244221982)
    expect(metrics.managementCostMinor + metrics.icCostMinor).toBe(metrics.totalCostMinor)
  })
  it('rounds source decimal salaries half-up, including carry to the next unit', () => {
    const org = loadOrganization('Employee Id,Manager,Name,Salary\na,,Root,1.005\nb,a,Report,9.99999\nc,a,Report,0.00499')
    expect([...org.employees.values()].map(e => e.salaryMinor)).toEqual([101, 1000, 0])
  })
})
