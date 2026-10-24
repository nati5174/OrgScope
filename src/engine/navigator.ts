import type { Organization } from './organization'
import { PAGE_SIZE, ancestorPath } from './explorer'
export type NavigatorRow = { id: string; key: string; depth: number; kind: 'employee' | 'pager'; position: number; siblings: number }

// Flatten expanded/paged nodes iteratively. The UI virtualizes this sequence,
// including extremely deep ancestor paths and forests with thousands of roots.
export function navigatorRows(org: Organization, expanded: ReadonlySet<string>, pages: ReadonlyMap<string, number>, pageSize = PAGE_SIZE): NavigatorRow[] {
  const stack: NavigatorRow[] = []
  for (let i = org.roots.length - 1; i >= 0; i--) stack.push({ id: org.roots[i], key: `employee:${org.roots[i]}`, depth: 0, kind: 'employee', position: i + 1, siblings: org.roots.length })
  const result: NavigatorRow[] = []
  while (stack.length) {
    const row = stack.pop()!; result.push(row)
    if (row.kind === 'pager' || !expanded.has(row.id)) continue
    const reports = org.children.get(row.id)!, start = (pages.get(row.id) ?? 0) * pageSize
    if (reports.length > pageSize) stack.push({ ...row, key: `page:${row.id}`, depth: row.depth + 1, kind: 'pager' })
    for (let i = Math.min(start + pageSize, reports.length) - 1; i >= start; i--) {
      stack.push({ id: reports[i], key: `employee:${reports[i]}`, kind: 'employee', depth: row.depth + 1, position: i + 1, siblings: reports.length })
    }
  }
  return result
}

export function revealInNavigator(org: Organization, id: string, expanded: ReadonlySet<string>, pages: ReadonlyMap<string, number>, pageSize = PAGE_SIZE) {
  const path = ancestorPath(org, id), nextExpanded = new Set(expanded), nextPages = new Map(pages)
  for (let i = 0; i < path.length - 1; i++) {
    nextExpanded.add(path[i]); nextPages.set(path[i], Math.floor(org.children.get(path[i])!.indexOf(path[i + 1]) / pageSize))
  }
  return { expanded: nextExpanded, pages: nextPages }
}
