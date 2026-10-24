import { readFileSync, writeFileSync } from 'node:fs'
import { cpus } from 'node:os'
import { loadOrganization, searchEmployees, type Timings } from '../src/engine/organization'
import { analyzeWorkforce } from '../src/engine/analytics'
import { simulateMove } from '../src/engine/scenario'
import { visibleNodes } from '../src/engine/explorer'
import { layoutTree } from '../src/engine/treeLayout'
const sizes = [1000, 10000, 40000, 100000]
const gc = (globalThis as { gc?: () => void }).gc
type Run = Timings & { searchMs: number; analyticsCalculationMs: number; scenarioCalculationMs: number; boundedLayoutMs: number; chartNodes: number; heapDeltaBytes: number; heapUsedBytes: number; rssBytes: number }
function csvFor(n: number) {
  if (n === 40000) return readFileSync('data/giga-corp-synthetic-40000.csv', 'utf8')
  const id = (i: number) => `GC${String(i + 1).padStart(6, '0')}`
  return 'employee_id,manager_id,name,salary,currency\n' + Array.from({ length: n }, (_, i) =>
    `${id(i)},${i ? id(Math.floor((i - 1) / 8)) : ''},Person ${i % 100},${65000 + i % 150000}.${String(i % 100).padStart(2, '0')},CAD`).join('\n')
}
function stats(values: number[]) {
  const sorted = [...values].sort((a, b) => a - b)
  return { median: (sorted[4] + sorted[5]) / 2, p95: sorted[Math.ceil(sorted.length * .95) - 1] }
}
const results = []
for (const count of sizes) {
  const csv = csvFor(count)
  if (count !== 40000) writeFileSync(`data/audit/performance-${count}.csv`, csv)
  loadOrganization(csv) // warmup
  const runs: Run[] = []
  for (let i = 0; i < 10; i++) {
    gc?.(); const before = process.memoryUsage().heapUsed
    const org = loadOrganization(csv), heap = process.memoryUsage().heapUsed
    let start = performance.now(); searchEmployees(org, 'no-such-employee'); const searchMs = performance.now() - start
    start = performance.now(); analyzeWorkforce(org, null); const analyticsCalculationMs = performance.now() - start
    const scenario = simulateMove(org, 'GC000002', 'GC000003')
    const expanded = new Set(org.employees.keys())
    start = performance.now(); const layout = layoutTree(visibleNodes(org, org.roots[0], expanded, new Map(), 150, 24)); const layoutMs = performance.now() - start
    runs.push({ ...org.timings, searchMs, analyticsCalculationMs, scenarioCalculationMs: scenario.calculationMs,
      boundedLayoutMs: layoutMs, chartNodes: layout.nodes.length, heapDeltaBytes: heap - before, heapUsedBytes: heap, rssBytes: process.memoryUsage().rss })
  }
  const metrics = ['parsingMs', 'constructionMs', 'aggregationMs', 'searchMs', 'analyticsCalculationMs', 'scenarioCalculationMs', 'boundedLayoutMs', 'heapDeltaBytes', 'heapUsedBytes', 'rssBytes'] as const
  results.push({ employees: count, dataset: count === 40000 ? 'Provided synthetic Giga Corp' : 'Audit-only synthetic balanced 8-way tree',
    summary: Object.fromEntries(metrics.map(key => [key, stats(runs.map(run => run[key]))])), rawRuns: runs })
  console.log(`Measured ${count} employees`)
}
const output = { runtime: process.version, cpu: cpus()[0].model, gcAvailable: !!gc,
  method: '10 sequential runs per size after 1 warmup. p95 uses nearest rank (with 10 samples this is the maximum; not a stable tail estimate). CSV already in memory. Heap delta sampled after processing, not peak memory. RSS is process-wide. Main-thread Node measurements exclude browser rendering.', results }
writeFileSync('data/audit/performance-node.json', JSON.stringify(output, null, 2) + '\n')
console.log(JSON.stringify(results.map(r => ({ employees: r.employees, summary: r.summary })), null, 2))
