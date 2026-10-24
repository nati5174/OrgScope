import { readFileSync, writeFileSync } from 'node:fs'
import { cpus } from 'node:os'
import { loadOrganization } from '../src/engine/organization'
import { visibleNodes } from '../src/engine/explorer'
import { navigatorRows } from '../src/engine/navigator'
import { layoutTree } from '../src/engine/treeLayout'
const org = loadOrganization(readFileSync(new URL('../data/giga-corp-synthetic-40000.csv', import.meta.url), 'utf8'))
const expanded = new Set(org.employees.keys()), pages = new Map<string, number>()
const calculate = () => layoutTree(visibleNodes(org, org.roots[0], expanded, pages, 150, 24))
calculate(); navigatorRows(org, expanded, pages, 24)
const runs = Array.from({ length: 10 }, () => {
  let start = performance.now()
  for (let i = 0; i < 100; i++) calculate()
  const projectionAndLayoutMs = (performance.now() - start) / 100
  start = performance.now(); const rows = navigatorRows(org, expanded, pages, 24)
  return { projectionAndLayoutMs, flattenFullyExpandedNavigatorMs: performance.now() - start, navigatorRows: rows.length }
})
const median = (values: number[]) => { values.sort((a, b) => a - b); return (values[4] + values[5]) / 2 }
const result = { dataset: 'Synthetic Giga Corp, 40000 employees. Original dataset unavailable.',
  cpu: cpus()[0].model, runtime: process.version,
  method: '1 warmup; 10 sequential runs. Each layout run averages 100 calculations of bounded 150-node projection + D3 tidy layout + orthogonal connectors. Navigator traversal deliberately expands all 40000 employees. No parsing or browser rendering included.',
  chartNodes: calculate().nodes.length,
  medianMs: { projectionAndLayout: median(runs.map(r => r.projectionAndLayoutMs)), flattenFullyExpandedNavigator: median(runs.map(r => r.flattenFullyExpandedNavigatorMs)) }, rawRuns: runs }
writeFileSync(new URL('../data/redesign/layout-benchmark-results.json', import.meta.url), JSON.stringify(result, null, 2) + '\n')
console.log(JSON.stringify(result, null, 2))
