import type { Metrics, Organization } from './organization'

export interface Scenario {
  organization: Organization; employeeId: string; destinationId: string; originalManagerId: string | null
  affectedIds: string[]; calculationMs: number
}
export function validateMove(org: Organization, employeeId: string, destinationId: string): string | null {
  const employee = org.employees.get(employeeId)
  if (!employee) return 'Choose an existing employee or team to move.'
  if (!org.employees.has(destinationId)) return 'Choose an existing destination manager.'
  if (employeeId === destinationId) return 'An employee cannot report to themselves.'
  if (employee.managerId === destinationId) return 'This team already reports to that manager.'
  let current: string | null = destinationId
  while (current !== null) {
    if (current === employeeId) return 'A team cannot move underneath one of its own descendants.'
    current = org.employees.get(current)!.managerId
  }
  return null
}
function ancestors(org: Organization, id: string | null): string[] {
  const result: string[] = []
  while (id !== null) { result.push(id); id = org.employees.get(id)!.managerId }
  return result
}

export function simulateMove(org: Organization, employeeId: string, destinationId: string): Scenario {
  const start = performance.now(), error = validateMove(org, employeeId, destinationId)
  if (error) throw new Error(error)
  const employee = org.employees.get(employeeId)!, oldParent = employee.managerId
  const oldPath = ancestors(org, oldParent), newPath = ancestors(org, destinationId)
  // Copy map indexes, sharing unchanged immutable records/arrays. Never mutate baseline.
  const employees = new Map(org.employees), children = new Map(org.children), metrics = new Map(org.metrics)
  employees.set(employeeId, { ...employee, managerId: destinationId })
  if (oldParent !== null) children.set(oldParent, org.children.get(oldParent)!.filter(id => id !== employeeId))
  children.set(destinationId, [...org.children.get(destinationId)!, employeeId])
  const affected = new Set([...oldPath, ...newPath])
  for (const id of affected) metrics.set(id, { ...org.metrics.get(id)! })
  const moved = org.metrics.get(employeeId)!, isManager = org.children.get(employeeId)!.length > 0
  const contribution: Metrics = {
    descendantCount: moved.descendantCount + 1,
    nonLeafDescendantCount: moved.nonLeafDescendantCount + Number(isManager),
    managementCostMinor: moved.managementCostMinor + (isManager ? employee.salaryMinor : 0),
    icCostMinor: moved.icCostMinor + (isManager ? 0 : employee.salaryMinor),
    totalCostMinor: moved.totalCostMinor + employee.salaryMinor,
  }
  function add(path: string[], delta: Metrics, sign: number) {
    for (const id of path) {
      const target = metrics.get(id)!
      for (const key of Object.keys(delta) as (keyof Metrics)[]) target[key] += sign * delta[key]
    }
  }
  add(oldPath, contribution, -1); add(newPath, contribution, 1)
  function reclassify(id: string, nowManager: boolean) {
    const salary = org.employees.get(id)!.salaryMinor, sign = nowManager ? 1 : -1
    add(ancestors(org, org.employees.get(id)!.managerId), {
      descendantCount: 0, nonLeafDescendantCount: sign,
      managementCostMinor: sign * salary, icCostMinor: -sign * salary, totalCostMinor: 0,
    }, 1)
  }
  if (oldParent !== null && children.get(oldParent)!.length === 0) reclassify(oldParent, false)
  if (org.children.get(destinationId)!.length === 0) reclassify(destinationId, true)
  // Check the final state, since intermediate deltas may temporarily be negative.
  for (const id of affected) {
    const m = metrics.get(id)!
    if (Object.values(m).some(value => !Number.isSafeInteger(value) || value < 0) || m.totalCostMinor !== m.managementCostMinor + m.icCostMinor) {
      throw new Error('Scenario totals exceed safe precision or failed reconciliation.')
    }
  }
  return { organization: { ...org, employees, children, metrics, roots: org.roots.filter(id => id !== employeeId) },
    employeeId, destinationId, originalManagerId: oldParent, affectedIds: [...affected], calculationMs: performance.now() - start }
}
