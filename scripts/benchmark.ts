import { readFileSync, writeFileSync } from 'node:fs'
import { cpus } from 'node:os'
import { loadOrganization, searchEmployees, type Timings } from '../src/engine/organization'
const text = readFileSync(new URL('../data data.csv', import.meta.url), 'utf8')
const runs: (Timings & { searchMs: number })[] = []
loadOrganization(text) // warm-up, excluded
for (let i = 0; i < 10; i++) {
  const org = loadOrganization(text)
  const start = performance.now()
  for (let j = 0; j < 100; j++) searchEmployees(org, j % 2 ? 'no-such-employee' : 'p_njwxPOk9vEs4ToOrLrA0m')
  runs.push({ ...org.timings, searchMs: (performance.now() - start) / 100 })
}
const median = (values: number[]) => { const sorted = values.sort((a,b) => a-b); return (sorted[4] + sorted[5]) / 2 }
const result = { dataset: 'Supplied assessment dataset; 40,000 rows', runtime: process.version,
  cpu: cpus()[0].model, platform: process.platform, runs: 10, warmups: 1,
  method: 'In-memory CSV; sequential runs; search mean per run over 100 queries alternating missing and final-row ID. No file I/O or browser rendering included.',
  medianMs: Object.fromEntries(['parsingMs', 'constructionMs', 'aggregationMs', 'searchMs'].map(key => [key, median(runs.map(r => r[key as keyof typeof r]))])),
  rawRuns: runs }
writeFileSync(new URL('../data/benchmark-results.json', import.meta.url), JSON.stringify(result, null, 2) + '\n')
console.log(JSON.stringify(result, null, 2))
