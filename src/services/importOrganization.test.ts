import { describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { importOrganization, type ImportWorker } from './importOrganization'
import { processImport } from '../workers/processImport'
import { DataValidationError, loadOrganization } from '../engine/organization'
import type { ImportMessage, ImportRequest } from '../workers/importProtocol'

class TestWorker implements ImportWorker {
  onmessage: ImportWorker['onmessage'] = null
  onerror: ImportWorker['onerror'] = null
  onmessageerror: ImportWorker['onmessageerror'] = null
  terminate = vi.fn()
  messages: ImportMessage[] = []
  constructor(private auto = true) {}
  emit(data: ImportMessage) { this.messages.push(data); this.onmessage?.(new MessageEvent('message', { data: structuredClone(data) })) }
  postMessage(request: ImportRequest) { if (this.auto) void processImport(request.file, message => this.emit(message)) }
}
const header = 'Employee Id,Manager,Name,Salary\n'
describe('background CSV import', () => {
  it('reports real import stages and bounded employee progress before publishing', async () => {
    const progress = vi.fn(), worker = new TestWorker()
    const csv = readFileSync(new URL('../../data data.csv', import.meta.url), 'utf8')
    const org = await importOrganization(new Blob([csv]), undefined, () => worker, progress)
    const updates = progress.mock.calls.map(([update]) => update)
    expect(updates.slice(0, 3).map(update => update.phase)).toEqual(['reading', 'calculating', 'assembling'])
    const assembly = updates.filter(update => update.phase === 'assembling')
    expect(assembly[0]).toMatchObject({ loaded: 0, total: 40000 })
    expect(assembly.at(-1)).toMatchObject({ loaded: org.employees.size, total: 40000 })
    for (let index = 1; index < assembly.length; index++) {
      expect(assembly[index].loaded).toBeGreaterThanOrEqual(assembly[index - 1].loaded)
      expect(assembly[index].loaded).toBeLessThanOrEqual(assembly[index].total)
    }
  })

  it('preserves engine metrics, reporting order, roots, IDs, and currency across worker serialization', async () => {
    const csv = header + 'c,b,"Ada, Jr",3.21\na,,Same,1.10\nb,a,Same,2.20\nz,,Other,0'
    const worker = new TestWorker(), result = await importOrganization(new Blob([csv]), undefined, () => worker)
    const expected = loadOrganization(csv)
    for (const field of ['employees', 'children', 'metrics', 'roots', 'currency'] as const) expect(result[field]).toEqual(expected[field])
    expect(worker.terminate).toHaveBeenCalledOnce()
    expect(worker.onmessage).toBeNull()
  })
  it('matches all 40k metrics without modifying the synchronous engine', async () => {
    const csv = readFileSync(new URL('../../data data.csv', import.meta.url), 'utf8')
    const worker = new TestWorker(), result = await importOrganization(new Blob([csv]), undefined, () => worker)
    const expected = loadOrganization(csv)
    expect(result.metrics).toEqual(expected.metrics); expect(result.children).toEqual(expected.children)
    expect(result.employees).toEqual(expected.employees); expect(result.roots).toEqual(expected.roots)
  })
  it('bounds messages for a wide team instead of cloning its full report list at once', async () => {
    const csv = header + 'r,,Root,1\n' + Array.from({ length: 5001 }, (_, i) => `${i},r,Employee ${i},1`).join('\n')
    const worker = new TestWorker(), result = await importOrganization(new Blob([csv]), undefined, () => worker)
    expect(result.children.get('r')).toHaveLength(5001)
    for (const message of worker.messages) {
      if (message.type === 'nodes') expect(message.employees.length).toBeLessThanOrEqual(500)
      if (message.type === 'edges') expect(message.edges.length).toBeLessThanOrEqual(1000)
    }
  })
  it('preserves complete validation issues and rejects malformed data', async () => {
    const worker = new TestWorker()
    await expect(importOrganization(new Blob([header + 'a,missing,A,1']), undefined, () => worker)).rejects.toBeInstanceOf(DataValidationError)
    expect(worker.terminate).toHaveBeenCalledOnce()
  })
  it('does not start a worker for an already aborted request', async () => {
    const controller = new AbortController(); controller.abort()
    const factory = vi.fn(() => new TestWorker())
    await expect(importOrganization(new Blob(), controller.signal, factory)).rejects.toMatchObject({ name: 'AbortError' })
    expect(factory).not.toHaveBeenCalled()
  })
  it('terminates on abort and ignores a late completed response', async () => {
    const worker = new TestWorker(false), controller = new AbortController()
    const promise = importOrganization(new Blob(), controller.signal, () => worker), lateMessage = worker.onmessage!
    controller.abort()
    lateMessage(new MessageEvent('message', { data: { type: 'complete', count: 0, currency: 'XXX', timings: { parsingMs: 0, constructionMs: 0, aggregationMs: 0 } } }))
    await expect(promise).rejects.toMatchObject({ name: 'AbortError' })
    expect(worker.terminate).toHaveBeenCalledOnce()
  })
  it('keeps partial chunks private and rejects if the worker subsequently fails', async () => {
    const worker = new TestWorker(false), published = vi.fn()
    const promise = importOrganization(new Blob(), undefined, () => worker)
    const outcome = promise.then(published, error => error)
    worker.emit({ type: 'nodes', employees: [{ id: 'partial', managerId: null, name: 'Partial', salaryMinor: 100 }],
      metrics: [{ descendantCount: 0, nonLeafDescendantCount: 0, managementCostMinor: 0, icCostMinor: 0, totalCostMinor: 0 }] })
    await Promise.resolve()
    expect(published).not.toHaveBeenCalled()
    worker.emit({ type: 'failure', message: 'Import interrupted' })
    expect(await outcome).toMatchObject({ message: 'Import interrupted' })
    expect(published).not.toHaveBeenCalled()
    expect(worker.terminate).toHaveBeenCalledOnce()
    expect(worker.onmessage).toBeNull()
  })
  it('isolates a replacement import from an aborted worker with partially received results', async () => {
    const oldWorker = new TestWorker(false), controller = new AbortController()
    const first = importOrganization(new Blob(), controller.signal, () => oldWorker)
    const rejected = expect(first).rejects.toMatchObject({ name: 'AbortError' })
    const lateMessage = oldWorker.onmessage!
    oldWorker.emit({ type: 'nodes', employees: [{ id: 'old', managerId: null, name: 'Old', salaryMinor: 100 }],
      metrics: [{ descendantCount: 0, nonLeafDescendantCount: 0, managementCostMinor: 0, icCostMinor: 0, totalCostMinor: 0 }] })
    controller.abort()
    const replacement = await importOrganization(new Blob([header + 'new,,New,2']), undefined, () => new TestWorker())
    lateMessage(new MessageEvent('message', { data: { type: 'complete', count: 1, currency: 'XXX',
      timings: { parsingMs: 0, constructionMs: 0, aggregationMs: 0 } } }))
    await rejected
    expect([...replacement.employees.keys()]).toEqual(['new'])
    expect(replacement.metrics.get('new')!.totalCostMinor).toBe(0)
    expect(oldWorker.terminate).toHaveBeenCalledOnce()
  })
  it('reports startup, worker runtime, deserialization, and incomplete-result failures', async () => {
    await expect(importOrganization(new Blob(), undefined, () => { throw new Error('startup') })).rejects.toThrow('Could not start')
    for (const mode of ['runtime', 'deserialize', 'incomplete']) {
      const worker = new TestWorker(false), promise = importOrganization(new Blob(), undefined, () => worker)
      if (mode === 'runtime') worker.onerror!(new Event('error') as ErrorEvent)
      else if (mode === 'deserialize') worker.onmessageerror!(new MessageEvent('messageerror'))
      else worker.emit({ type: 'complete', count: 1, currency: 'XXX', timings: { parsingMs: 0, constructionMs: 0, aggregationMs: 0 } })
      await expect(promise).rejects.toThrow(/import|Import/)
      expect(worker.terminate).toHaveBeenCalledOnce()
    }
  })
})
