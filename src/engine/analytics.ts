import type { Organization } from './organization'

export interface Bucket { label: string; count: number }
export interface Branch { id: string; headcount: number; managers: number; totalCostMinor: number; managementCostMinor: number }
export interface WorkforceAnalytics {
  headcount: number; managers: number; ics: number; totalCostMinor: number
  managementCostMinor: number; icCostMinor: number; averageSalaryMinor: number
  minSalaryMinor: number; maxSalaryMinor: number; maxDepth: number; managementLayers: number
  averageSpan: number | null; salaryBuckets: (Bucket & { minMinor: number; maxMinor: number })[]
  depthBuckets: Bucket[]; spanBuckets: Bucket[]; branches: Branch[]; leaderCostMinor: number
}

// Scope null is the whole forest. A selected employee's scope includes that employee.
// No department assumptions: disjoint reporting branches are comparable across CSV schemas.
export function analyzeWorkforce(org: Organization, scope: string | null): WorkforceAnalytics {
  if (scope !== null && !org.employees.has(scope)) throw new Error(`Unknown analytics scope: ${scope}`)
  const stack = (scope ? [scope] : org.roots).map(id => ({ id, depth: 0 }))
  let headcount = 0, managers = 0, totalCostMinor = 0, managementCostMinor = 0
  let minSalaryMinor = Infinity, maxSalaryMinor = 0, maxDepth = 0, reportCount = 0
  const salaries: number[] = [], depths = new Map<number, number>(), managementDepths = new Set<number>()
  const spanBuckets = [
    { label: '1 report', count: 0 }, { label: '2–4 reports', count: 0 }, { label: '5–8 reports', count: 0 },
    { label: '9–12 reports', count: 0 }, { label: '13–20 reports', count: 0 }, { label: '21+ reports', count: 0 },
  ]
  while (stack.length) {
    const { id, depth } = stack.pop()!, employee = org.employees.get(id)!, reports = org.children.get(id)!
    headcount++; totalCostMinor += employee.salaryMinor; salaries.push(employee.salaryMinor)
    if (!Number.isSafeInteger(totalCostMinor)) throw new Error('Analytics salary total exceeds safe integer precision')
    minSalaryMinor = Math.min(minSalaryMinor, employee.salaryMinor); maxSalaryMinor = Math.max(maxSalaryMinor, employee.salaryMinor)
    maxDepth = Math.max(maxDepth, depth); depths.set(depth, (depths.get(depth) ?? 0) + 1)
    if (reports.length) {
      managers++; managementCostMinor += employee.salaryMinor; reportCount += reports.length; managementDepths.add(depth)
      const span = reports.length
      spanBuckets[span === 1 ? 0 : span <= 4 ? 1 : span <= 8 ? 2 : span <= 12 ? 3 : span <= 20 ? 4 : 5].count++
    }
    for (const child of reports) stack.push({ id: child, depth: depth + 1 })
  }
  // Equal-width integer-cent buckets, including a dedicated single-value case.
  const bucketCount = minSalaryMinor === maxSalaryMinor ? 1 : 8
  const bucketWidth = Math.max(1, Math.ceil((maxSalaryMinor - minSalaryMinor + 1) / bucketCount))
  const salaryBuckets = Array.from({ length: bucketCount }, (_, i) => ({ label: `Salary band ${i + 1}`, count: 0,
    minMinor: minSalaryMinor + i * bucketWidth, maxMinor: Math.min(maxSalaryMinor, minSalaryMinor + (i + 1) * bucketWidth - 1) }))
    .filter(b => b.minMinor <= b.maxMinor)
  for (const salary of salaries) salaryBuckets[Math.min(salaryBuckets.length - 1, Math.floor((salary - minSalaryMinor) / bucketWidth))].count++
  const depthBuckets: Bucket[] = Array.from({ length: Math.min(maxDepth + 1, 11) }, (_, i) => ({ label: i === 10 ? 'Level 10+' : `Level ${i}`, count: 0 }))
  for (const [depth, count] of depths) depthBuckets[Math.min(depth, 10)].count += count
  const branchIds = scope ? org.children.get(scope)! : org.roots.length === 1 ? org.children.get(org.roots[0])! : org.roots
  const leaderId = scope ?? (org.roots.length === 1 ? org.roots[0] : null)
  const branches = branchIds.map((id): Branch => {
    const employee = org.employees.get(id)!, metrics = org.metrics.get(id)!, isManager = org.children.get(id)!.length > 0
    return { id, headcount: metrics.descendantCount + 1, managers: metrics.nonLeafDescendantCount + Number(isManager),
      totalCostMinor: metrics.totalCostMinor + employee.salaryMinor,
      managementCostMinor: metrics.managementCostMinor + (isManager ? employee.salaryMinor : 0) }
  }).sort((a, b) => b.totalCostMinor - a.totalCostMinor || a.id.localeCompare(b.id))
  return { headcount, managers, ics: headcount - managers, totalCostMinor, managementCostMinor,
    icCostMinor: totalCostMinor - managementCostMinor, averageSalaryMinor: totalCostMinor / headcount,
    minSalaryMinor, maxSalaryMinor, maxDepth, managementLayers: managementDepths.size,
    averageSpan: managers ? reportCount / managers : null,
    salaryBuckets, depthBuckets, spanBuckets, branches, leaderCostMinor: leaderId ? org.employees.get(leaderId)!.salaryMinor : 0 }
}
