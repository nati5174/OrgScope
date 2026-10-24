import type { Organization } from './organization'
export const PAGE_SIZE = 8
export const NODE_LIMIT = 150
export interface VisibleNode { id: string; depth: number; parentId: string | null }

export function ancestorPath(org: Organization, id: string): string[] {
  const path: string[] = []
  let current = org.employees.get(id)
  while (current) {
    path.push(current.id)
    current = current.managerId ? org.employees.get(current.managerId) : undefined
  }
  return path.reverse()
}

export function visibleNodes(org: Organization, focus: string, expanded: ReadonlySet<string>, pages: ReadonlyMap<string, number>, limit = NODE_LIMIT, pageSize = PAGE_SIZE): VisibleNode[] {
  if (!org.employees.has(focus)) return []
  const queue: VisibleNode[] = [{ id: focus, depth: 0, parentId: null }], result: VisibleNode[] = []
  // Breadth first keeps siblings visible before deeper expansions consume the budget.
  for (let cursor = 0; cursor < queue.length && result.length < limit; cursor++) {
    const node = queue[cursor]
    result.push(node)
    if (!expanded.has(node.id)) continue
    const reports = org.children.get(node.id) ?? []
    const start = (pages.get(node.id) ?? 0) * pageSize
    for (const id of reports.slice(start, start + pageSize)) {
      if (queue.length >= limit) break
      queue.push({ id, depth: node.depth + 1, parentId: node.id })
    }
  }
  return result
}

export function revealEmployee(org: Organization, id: string) {
  const path = ancestorPath(org, id)
  const pages = new Map<string, number>()
  for (let i = 0; i < path.length - 1; i++) {
    pages.set(path[i], Math.floor(org.children.get(path[i])!.indexOf(path[i + 1]) / PAGE_SIZE))
  }
  // Focus on the parent: even a path thousands of levels deep remains bounded.
  const focus = path.length > 1 ? path[path.length - 2] : id
  return { focus, pages, expanded: new Set([focus]) }
}
