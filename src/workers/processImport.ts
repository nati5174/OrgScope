import { DataValidationError, loadOrganization } from '../engine/organization'
import type { Employee, Metrics } from '../engine/organization'
import type { ImportMessage } from './importProtocol'

// Run exclusively in the worker. Use the existing parser/engine without changing
// their calculations. Small messages avoid one expensive whole-graph clone on UI.
export async function processImport(file: Blob, send: (message: ImportMessage) => void) {
  try {
    send({ type: 'progress', progress: { phase: 'reading' } })
    const text = await file.text()
    send({ type: 'progress', progress: { phase: 'calculating' } })
    const org = loadOrganization(text)
    send({ type: 'progress', progress: { phase: 'assembling', loaded: 0, total: org.employees.size } })
    let employees: Employee[] = [], metrics: Metrics[] = []
    for (const employee of org.employees.values()) {
      employees.push(employee); metrics.push(org.metrics.get(employee.id)!)
      if (employees.length === 500) { send({ type: 'nodes', employees, metrics }); employees = []; metrics = [] }
    }
    if (employees.length) send({ type: 'nodes', employees, metrics })
    let edges: [string, string][] = []
    for (const [manager, reports] of org.children) {
      for (const report of reports) {
        edges.push([manager, report])
        if (edges.length === 1000) { send({ type: 'edges', edges }); edges = [] }
      }
    }
    if (edges.length) send({ type: 'edges', edges })
    send({ type: 'complete', count: org.employees.size, currency: org.currency, timings: org.timings })
  } catch (error) {
    send({ type: 'failure', message: error instanceof Error ? error.message : String(error),
      issues: error instanceof DataValidationError ? error.issues : undefined })
  }
}
