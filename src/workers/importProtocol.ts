import type { Employee, Metrics, Timings } from '../engine/organization'

export interface ImportRequest { file: Blob }
export interface ImportProgress { phase: 'reading' | 'calculating' | 'assembling'; loaded?: number; total?: number }
export type ImportMessage =
  | { type: 'progress'; progress: ImportProgress }
  | { type: 'nodes'; employees: Employee[]; metrics: Metrics[] }
  | { type: 'edges'; edges: [string, string][] }
  | { type: 'complete'; count: number; currency: string; timings: Timings }
  | { type: 'failure'; message: string; issues?: string[] }
