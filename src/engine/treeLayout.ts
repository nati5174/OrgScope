import { stratify, tree } from 'd3-hierarchy'
import type { VisibleNode } from './explorer'

export const CARD_WIDTH = 220
export const CARD_HEIGHT = 112
export const SIBLING_GAP = 18
export const LEVEL_GAP = 56
export interface PositionedNode extends VisibleNode { x: number; y: number }
export interface Connector { id: string; path: string; segments: [number, number, number, number][] }
export function layoutTree(nodes: VisibleNode[]) {
  if (!nodes.length) return { nodes: [] as PositionedNode[], connectors: [] as Connector[], width: 0, height: 0 }
  const root = stratify<VisibleNode>().id(n => n.id).parentId(n => n.parentId)(nodes)
  const tidy = tree<VisibleNode>().nodeSize([CARD_HEIGHT + SIBLING_GAP, CARD_WIDTH + LEVEL_GAP])
    .separation((a, b) => a.parent === b.parent ? 1 : 1.15)(root)
  const all = tidy.descendants(), minX = Math.min(...all.map(n => n.x))
  const positioned = all.map(n => ({ ...n.data, x: n.y + 24, y: n.x - minX + 24 }))
  const byId = new Map(positioned.map(n => [n.id, n]))
  const connectors = positioned.filter(n => n.parentId).map((n): Connector => {
    const parent = byId.get(n.parentId!)!, sx = parent.x + CARD_WIDTH, sy = parent.y + CARD_HEIGHT / 2
    const endX = n.x, endY = n.y + CARD_HEIGHT / 2, midX = (sx + endX) / 2
    return { id: n.id, path: `M ${sx} ${sy} H ${midX} V ${endY} H ${endX}`,
      segments: [[sx, sy, midX, sy], [midX, sy, midX, endY], [midX, endY, endX, endY]] }
  })
  return { nodes: positioned, connectors,
    width: Math.max(...positioned.map(n => n.x + CARD_WIDTH)) + 24,
    height: Math.max(...positioned.map(n => n.y + CARD_HEIGHT)) + 24 }
}
