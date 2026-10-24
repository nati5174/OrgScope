import { processImport } from './processImport'
import type { ImportRequest, ImportMessage } from './importProtocol'
const scope = self as unknown as {
  onmessage: ((event: MessageEvent<ImportRequest>) => void) | null
  postMessage: (message: ImportMessage) => void
}
scope.onmessage = event => { void processImport(event.data.file, message => scope.postMessage(message)) }
