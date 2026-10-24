import { readFileSync, writeFileSync } from 'node:fs'
import { cpus } from 'node:os'
import { loadOrganization } from '../src/engine/organization'
import { analyzeWorkforce } from '../src/engine/analytics'
const org = loadOrganization(readFileSync(new URL('../data/giga-corp-synthetic-40000.csv', import.meta.url), 'utf8'))
analyzeWorkforce(org, null)
const runs: number[] = []
for (let i = 0; i < 10; i++) {
  const start = performance.now()
  analyzeWorkforce(org, null)
  runs.push(performance.now() - start)
}
const sorted = [...runs].sort((a, b) => a - b)
const result = { dataset: 'Synthetic Giga Corp, 40000 employees', runtime: process.version, cpu: cpus()[0].model,
  method: 'Whole-organization analytics; 1 warmup, 10 sequential runs. Excludes CSV parsing, engine construction, and browser rendering.',
  medianMs: (sorted[4] + sorted[5]) / 2, rawRunsMs: runs }
writeFileSync(new URL('../data/analytics-benchmark-results.json', import.meta.url), JSON.stringify(result, null, 2) + '\n')
console.log(JSON.stringify(result, null, 2))
