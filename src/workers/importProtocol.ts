import type { Employee, Metrics, Timings } from '../engine/organization'

export interface ImportRequest { file: Blob }
export type ImportMessage =
  | { type: 'nodes'; employees: Employee[]; metrics: Metrics[] }
  | { type: 'edges'; edges: [string, string][] }
  | { type: 'complete'; count: number; currency: string; timings: Timings }
  | { type: 'failure'; message: string; issues?: string[] }
