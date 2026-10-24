import { readFileSync, writeFileSync } from 'node:fs'
import { cpus } from 'node:os'
import { loadOrganization } from '../src/engine/organization'
import { simulateMove } from '../src/engine/scenario'
const org = loadOrganization(readFileSync(new URL('../data/giga-corp-synthetic-40000.csv', import.meta.url), 'utf8'))
simulateMove(org, 'GC000002', 'GC000007')
const runs = Array.from({ length: 10 }, () => simulateMove(org, 'GC000002', 'GC000007').calculationMs)
const sorted = [...runs].sort((a, b) => a - b)
const result = { dataset: 'Synthetic Giga Corp, 40000 employees', runtime: process.version, cpu: cpus()[0].model,
  move: 'GC000002 under GC000007', method: '1 warmup, 10 sequential independent previews. Includes validation, shallow map copies, and affected-path metric updates. Excludes loading and browser rendering.',
  medianMs: (sorted[4] + sorted[5]) / 2, rawRunsMs: runs }
writeFileSync(new URL('../data/scenario-benchmark-results.json', import.meta.url), JSON.stringify(result, null, 2) + '\n')
console.log(JSON.stringify(result, null, 2))
