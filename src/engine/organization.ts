import Papa from 'papaparse'

export interface Employee {
  id: string; managerId: string | null; name: string; salaryMinor: number
  department?: string; title?: string; location?: string
}
export interface Metrics {
  descendantCount: number; nonLeafDescendantCount: number
  managementCostMinor: number; icCostMinor: number; totalCostMinor: number
}
export interface Timings { parsingMs: number; constructionMs: number; aggregationMs: number }
export interface Organization {
  employees: Map<string, Employee>; children: Map<string, string[]>
  roots: string[]; metrics: Map<string, Metrics>; currency: string; timings: Timings
}
export class DataValidationError extends Error {
  constructor(public issues: string[]) { super(issues.slice(0, 20).join('\n')); this.name = 'DataValidationError' }
}
const emptyMetrics = (): Metrics => ({ descendantCount: 0, nonLeafDescendantCount: 0, managementCostMinor: 0, icCostMinor: 0, totalCostMinor: 0 })

export function parseCsv(text: string): { employees: Employee[]; currency: string } {
  const result = Papa.parse<Record<string, string>>(text.replace(/^\uFEFF/, ''), {
    header: true, skipEmptyLines: 'greedy', transformHeader: h => h.trim(),
  })
  const issues = result.errors.map(e => `CSV row ${e.row === undefined ? '?' : e.row + 2}: ${e.message}`)
  for (const header of Object.values(result.meta.renamedHeaders ?? {})) issues.push(`Duplicate CSV column: ${header}`)
  for (const field of ['employee_id', 'manager_id', 'name', 'salary', 'currency']) {
    if (!result.meta.fields?.includes(field)) issues.push(`Missing required column: ${field}`)
  }
  const currencies = new Set<string>()
  const employees = result.data.map((row, index): Employee => {
    const salary = row.salary?.trim() ?? ''
    let salaryMinor = NaN
    if (/^\d+(\.\d{1,2})?$/.test(salary)) {
      const [whole, fraction = ''] = salary.split('.')
      const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2, '0'))
      if (cents <= BigInt(Number.MAX_SAFE_INTEGER)) salaryMinor = Number(cents)
    }
    if (!/^\d+(\.\d{1,2})?$/.test(salary) || !Number.isSafeInteger(salaryMinor)) issues.push(`Row ${index + 2}: invalid salary`)
    const currency = row.currency?.trim() ?? ''
    if (!/^[A-Z]{3}$/.test(currency)) issues.push(`Row ${index + 2}: currency must be a three-letter uppercase code`)
    currencies.add(currency)
    return { id: row.employee_id?.trim() ?? '', managerId: row.manager_id?.trim() || null,
      name: row.name?.trim() ?? '', salaryMinor,
      department: row.department?.trim(), title: row.title?.trim(), location: row.location?.trim() }
  })
  if (!employees.length) issues.push('Dataset contains no employees')
  if (currencies.size > 1) issues.push('Mixed currencies cannot be aggregated without conversion')
  if (issues.length) throw new DataValidationError(issues)
  return { employees, currency: [...currencies][0] }
}

export function buildOrganization(input: readonly Employee[], currency = 'CAD'): Organization {
  const start = performance.now()
  const employees = new Map<string, Employee>(), children = new Map<string, string[]>()
  const issues: string[] = [], roots: string[] = []
  let companySalary = 0
  for (const employee of input) {
    if (!employee.id || !employee.name) issues.push('Every employee needs an ID and name')
    if (employees.has(employee.id)) issues.push(`Duplicate employee ID: ${employee.id}`)
    if (!Number.isSafeInteger(employee.salaryMinor) || employee.salaryMinor < 0) issues.push(`Invalid salary: ${employee.id}`)
    companySalary += employee.salaryMinor
    employees.set(employee.id, { ...employee }); children.set(employee.id, [])
  }
  if (!input.length) issues.push('Dataset contains no employees')
  if (!Number.isSafeInteger(companySalary)) issues.push('Company salary total exceeds safe integer precision')
  for (const employee of employees.values()) {
    if (employee.managerId === null) roots.push(employee.id)
    else if (!employees.has(employee.managerId)) issues.push(`Missing manager ${employee.managerId} for ${employee.id}`)
    else children.get(employee.managerId)!.push(employee.id)
  }
  if (issues.length) throw new DataValidationError(issues)
  // Leaf-to-root queue: iterative postorder, including cycle detection in disconnected components.
  const remaining = new Map([...children].map(([id, reports]) => [id, reports.length]))
  const queue = [...employees.keys()].filter(id => remaining.get(id) === 0)
  const metrics = new Map([...employees.keys()].map(id => [id, emptyMetrics()]))
  const constructionMs = performance.now() - start
  const aggregateStart = performance.now()
  for (let cursor = 0; cursor < queue.length; cursor++) {
    const id = queue[cursor], employee = employees.get(id)!, own = metrics.get(id)!
    if (employee.managerId === null) continue
    const parent = metrics.get(employee.managerId)!, isManager = children.get(id)!.length > 0
    parent.descendantCount += 1 + own.descendantCount
    parent.nonLeafDescendantCount += Number(isManager) + own.nonLeafDescendantCount
    parent.managementCostMinor += own.managementCostMinor + (isManager ? employee.salaryMinor : 0)
    parent.icCostMinor += own.icCostMinor + (isManager ? 0 : employee.salaryMinor)
    parent.totalCostMinor = parent.managementCostMinor + parent.icCostMinor
    if (!Number.isSafeInteger(parent.totalCostMinor)) throw new DataValidationError(['Aggregate salary exceeds safe integer precision'])
    const count = remaining.get(employee.managerId)! - 1
    remaining.set(employee.managerId, count)
    if (count === 0) queue.push(employee.managerId)
  }
  if (queue.length !== employees.size) throw new DataValidationError(['Cyclic reporting relationships detected'])
  return { employees, children, roots, metrics, currency,
    timings: { parsingMs: 0, constructionMs, aggregationMs: performance.now() - aggregateStart } }
}

export function loadOrganization(text: string): Organization {
  const start = performance.now(), parsed = parseCsv(text), parsingMs = performance.now() - start
  const org = buildOrganization(parsed.employees, parsed.currency)
  org.timings.parsingMs = parsingMs
  return org
}

export function searchEmployees(org: Organization, query: string, limit = 30): Employee[] {
  const needle = query.trim().toLocaleLowerCase()
  if (!needle || limit <= 0) return []
  const found: Employee[] = []
  for (const employee of org.employees.values()) {
    if (employee.id.toLocaleLowerCase().includes(needle) || employee.name.toLocaleLowerCase().includes(needle)) {
      found.push(employee)
      if (found.length >= limit) break
    }
  }
  return found
}

// Null means no manager salary exists; the UI should display N/A.
export function managementCostRatio(metrics: Metrics): number | null {
  return metrics.managementCostMinor === 0 ? null : metrics.icCostMinor / metrics.managementCostMinor
}
