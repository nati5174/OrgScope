import { spawnSync } from 'node:child_process'
import { readFileSync, writeFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { loadOrganization, managementCostRatio, type Metrics } from '../src/engine/organization'
import { ancestorPath } from '../src/engine/explorer'
import { analyzeWorkforce } from '../src/engine/analytics'
import { simulateMove } from '../src/engine/scenario'
const csvPath = 'data data.csv', csv = readFileSync(csvPath, 'utf8')
const oracle = spawnSync('python', ['scripts/reference_metrics.py', csvPath], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
if (oracle.status !== 0) throw new Error(oracle.stderr)
const reference = JSON.parse(oracle.stdout) as { metrics: Record<string, Metrics>; directReports: Record<string, number>; depth: Record<string, number>; parents: Record<string, string | null>; roots: string[]; headcount: number; totalSalaryMinor: number }
const org = loadOrganization(csv), mismatches: { id: string; field: string }[] = []
let employeesWithMismatch = 0, comparisons = 0
for (const [id, expected] of Object.entries(reference.metrics)) {
  const actual = org.metrics.get(id)!, before = mismatches.length
  for (const field of Object.keys(expected) as (keyof Metrics)[]) {
    comparisons++; if (actual[field] !== expected[field]) mismatches.push({ id, field })
  }
  const ratio = expected.managementCostMinor ? expected.icCostMinor / expected.managementCostMinor : null
  for (const [field, matches] of [
    ['directReports', org.children.get(id)!.length === (reference.directReports[id] ?? 0)],
    ['parent', org.employees.get(id)!.managerId === reference.parents[id]],
    ['depth', ancestorPath(org, id).length - 1 === reference.depth[id]],
    ['ratio', managementCostRatio(actual) === ratio],
    ['reconciliation', actual.managementCostMinor + actual.icCostMinor === actual.totalCostMinor],
    ['nonLeafBound', actual.nonLeafDescendantCount <= actual.descendantCount],
    ['leaf', org.children.get(id)!.length > 0 || actual.descendantCount === 0],
  ] as const) { comparisons++; if (!matches) mismatches.push({ id, field }) }
  if (mismatches.length > before) employeesWithMismatch++
}
if (JSON.stringify(org.roots) !== JSON.stringify(reference.roots)) mismatches.push({ id: '*', field: 'roots' })
const analytics = analyzeWorkforce(org, null)
if (analytics.headcount !== reference.headcount || analytics.totalCostMinor !== reference.totalSalaryMinor) mismatches.push({ id: '*', field: 'analytics' })
// Verify repeated independent moves preserve baseline and whole-company totals.
const snapshot = JSON.stringify([...org.metrics]), scenarioChecks = []
for (const [moving, destination] of [['p_cNNDKZRLm2DMkjKXx8YPdo', 'p_XkJbblsKUlQoR5W1DxAN7t'], ['p_XkJbblsKUlQoR5W1DxAN7t', 'p_P7lSz8GTk0HF8V8d0Ra6E'], ['p_njwxPOk9vEs4ToOrLrA0m', 'p_DrnEHzsrxaHOPnwwNDBwy']]) {
  const scenario = simulateMove(org, moving, destination), proposed = analyzeWorkforce(scenario.organization, null)
  const independent = spawnSync('python', ['scripts/reference_metrics.py', csvPath, moving, destination], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
  if (independent.status !== 0) throw new Error(independent.stderr)
  const expected = JSON.parse(independent.stdout) as typeof reference
  let scenarioMismatches = 0, metricComparisons = 0
  for (const [id, metrics] of Object.entries(expected.metrics)) {
    for (const field of Object.keys(metrics) as (keyof Metrics)[]) {
      metricComparisons++
      if (scenario.organization.metrics.get(id)![field] !== metrics[field]) scenarioMismatches++
    }
  }
  scenarioChecks.push({ moving, destination, headcountPreserved: proposed.headcount === reference.headcount,
    salaryPreserved: proposed.totalCostMinor === reference.totalSalaryMinor, baselineUnchanged: JSON.stringify([...org.metrics]) === snapshot,
    metricComparisons, independentMetricMismatches: scenarioMismatches })
}
const result = { dataset: csvPath, originalDatasetAvailable: true,
  sha256: createHash('sha256').update(csv).digest('hex'), employeesVerified: org.employees.size,
  referenceMethod: 'Independent Python CSV + Decimal; deposit each salary into its raw ancestor chain, with per-chain cycle and duplicate detection.',
  comparisons, employeesWithMismatch, mismatches: mismatches.length, examples: mismatches.slice(0, 20), scenarioChecks }
writeFileSync('data/audit/math-results.json', JSON.stringify(result, null, 2) + '\n')
console.log(JSON.stringify(result, null, 2))
if (mismatches.length || scenarioChecks.some(s => !s.headcountPreserved || !s.salaryPreserved || !s.baselineUnchanged || s.independentMetricMismatches)) process.exitCode = 1
