import { DataValidationError, type Employee, type Metrics, type Organization } from '../engine/organization'
import type { ImportMessage, ImportRequest, ImportProgress } from '../workers/importProtocol'

export interface ImportWorker {
  onmessage: ((event: MessageEvent<ImportMessage>) => void) | null
  onerror: ((event: ErrorEvent) => void) | null
  onmessageerror: ((event: MessageEvent) => void) | null
  postMessage: (request: ImportRequest) => void
  terminate: () => void
}
const createWorker = (): ImportWorker => new Worker(new URL('../workers/import.worker.ts', import.meta.url), { type: 'module' })

// Assemble indexes from bounded chunks; never parse or recompute metrics here.
// A private organization is published only after a successful complete message.
export function importOrganization(file: Blob, signal?: AbortSignal, factory = createWorker, onProgress?: (progress: ImportProgress) => void): Promise<Organization> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(new DOMException('Import cancelled', 'AbortError')); return }
    let worker: ImportWorker
    try { worker = factory() }
    catch { reject(new Error('Could not start background CSV import. Please retry in a browser with Web Worker support.')); return }
    const employees = new Map<string, Employee>(), children = new Map<string, string[]>(), metrics = new Map<string, Metrics>(), roots: string[] = []
    let settled = false, total = 0
    function cleanup() {
      worker.onmessage = null; worker.onerror = null; worker.onmessageerror = null
      worker.terminate(); signal?.removeEventListener('abort', abort)
    }
    function fail(error: Error) { if (!settled) { settled = true; cleanup(); reject(error) } }
    function abort() { fail(new DOMException('Import cancelled', 'AbortError')) }
    signal?.addEventListener('abort', abort, { once: true })
    worker.onerror = () => fail(new Error('Background CSV import failed. Please retry.'))
    worker.onmessageerror = () => fail(new Error('Could not read background import results. Please retry.'))
    worker.onmessage = ({ data }) => {
      if (settled) return
      if (data.type === 'progress') { total = data.progress.total ?? total; onProgress?.(data.progress); return }
      if (data.type === 'failure') { fail(data.issues ? new DataValidationError(data.issues) : new Error(data.message)); return }
      if (data.type === 'nodes') {
        for (let i = 0; i < data.employees.length; i++) {
          const employee = data.employees[i]
          employees.set(employee.id, employee); children.set(employee.id, []); metrics.set(employee.id, data.metrics[i])
          if (employee.managerId === null) roots.push(employee.id)
        }
        onProgress?.({ phase: 'assembling', loaded: employees.size, total })
      } else if (data.type === 'edges') {
        for (const [manager, report] of data.edges) children.get(manager)!.push(report)
      } else {
        if (employees.size !== data.count) { fail(new Error('Background import returned incomplete employee data. Please retry.')); return }
        settled = true; cleanup()
        resolve({ employees, children, metrics, roots, currency: data.currency, timings: data.timings })
      }
    }
    try { worker.postMessage({ file }) }
    catch { fail(new Error('Could not send the CSV to the background importer. Please retry.')) }
  })
}
