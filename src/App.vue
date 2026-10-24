<script setup lang="ts">
import { shallowRef, ref, nextTick, onBeforeUnmount } from 'vue'
import type { Organization } from './engine/organization'
import { importOrganization } from './services/importOrganization'
import OrganizationExplorer from './components/OrganizationExplorer.vue'
import WorkforceAnalytics from './components/WorkforceAnalytics.vue'
import ScenarioPlanner from './components/ScenarioPlanner.vue'
const org = shallowRef<Organization | null>(null)
const view = ref<'explorer' | 'analytics' | 'planner'>('explorer'), analyticsScope = ref<string | null>(null), explorerTarget = ref<string | null>(null)
const busy = ref(false), error = ref(''), generation = ref(0), datasetName = ref('')
let activeImport: AbortController | null = null
async function ingest(file: Blob, name: string, controller: AbortController) {
  const next = await importOrganization(file, controller.signal)
  if (activeImport !== controller || controller.signal.aborted) return
  org.value = next; datasetName.value = name; generation.value++
  analyticsScope.value = null; explorerTarget.value = null
}
function analyze(id: string) { analyticsScope.value = id; view.value = 'analytics' }
async function explore(id: string) { explorerTarget.value = null; view.value = 'explorer'; await nextTick(); explorerTarget.value = id }
async function sample() {
  activeImport?.abort()
  const controller = new AbortController(); activeImport = controller
  busy.value = true; error.value = ''
  try {
    const response = await fetch(new URL('../data/giga-corp-synthetic-40000.csv', import.meta.url), { signal: controller.signal })
    if (!response.ok) throw new Error('Could not load the sample dataset')
    await ingest(await response.blob(), 'Giga Corp · Synthetic sample', controller)
  } catch (e) { if (!controller.signal.aborted && activeImport === controller) error.value = e instanceof Error ? e.message : String(e) }
  finally { if (activeImport === controller) { busy.value = false; activeImport = null } }
}
async function upload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  activeImport?.abort()
  const controller = new AbortController(); activeImport = controller
  busy.value = true; error.value = ''
  try { await ingest(file, file.name, controller) }
  catch (e) { if (!controller.signal.aborted && activeImport === controller) error.value = e instanceof Error ? e.message : String(e) }
  finally { if (activeImport === controller) { busy.value = false; activeImport = null }; (event.target as HTMLInputElement).value = '' }
}
onBeforeUnmount(() => activeImport?.abort())
</script>

<template>
  <div class="min-h-screen">
    <header class="border-b border-slate-200 bg-white px-5 py-4 sm:px-8">
      <div class="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-4">
        <a href="/" class="text-xl font-semibold tracking-tight"><span class="mr-2 text-blue-700">◈</span>OrgScope</a>
        <div class="flex flex-wrap items-center gap-3 text-xs">
          <span v-if="org" class="rounded-full bg-blue-50 px-3 py-2 font-medium text-blue-800">{{ org.employees.size.toLocaleString() }} employees validated</span>
          <button :disabled="busy" class="toolbar" @click="sample">{{ busy ? 'Processing…' : org ? 'Reload sample' : 'Load Giga Corp sample' }}</button>
          <label class="toolbar cursor-pointer">Upload CSV<input :disabled="busy" type="file" accept=".csv,text/csv" class="sr-only" @change="upload"></label>
        </div>
      </div>
    </header>
    <main class="mx-auto max-w-[1600px] px-4 pb-10 sm:px-8">
      <pre v-if="error" role="alert" class="mt-5 whitespace-pre-wrap rounded-xl bg-red-50 p-4 text-sm text-red-800">{{ error }}</pre>
      <template v-if="org">
        <nav aria-label="Workspace views" class="mt-5 flex flex-wrap gap-2 border-b border-slate-200 pb-3 text-sm">
          <button class="rounded-lg px-4 py-2 font-medium" :class="view === 'explorer' ? 'bg-blue-800 text-white' : 'text-slate-600 hover:bg-white'" :aria-current="view === 'explorer' ? 'page' : undefined" @click="view = 'explorer'">Organization Explorer</button>
          <button class="rounded-lg px-4 py-2 font-medium" :class="view === 'analytics' ? 'bg-blue-800 text-white' : 'text-slate-600 hover:bg-white'" :aria-current="view === 'analytics' ? 'page' : undefined" @click="view = 'analytics'">Workforce Analytics</button>
          <button class="rounded-lg px-4 py-2 font-medium" :class="view === 'planner' ? 'bg-blue-800 text-white' : 'text-slate-600 hover:bg-white'" :aria-current="view === 'planner' ? 'page' : undefined" @click="view = 'planner'">Scenario Planner</button>
        </nav>
        <OrganizationExplorer v-show="view === 'explorer'" :key="`explorer-${generation}`" :org="org" :requested-employee="explorerTarget" @analyze="analyze" />
        <WorkforceAnalytics v-if="view === 'analytics'" :org="org" :scope="analyticsScope" @scope="id => analyticsScope = id" @explore="explore" />
        <ScenarioPlanner v-show="view === 'planner'" :key="`planner-${generation}`" :org="org" />
      </template>
      <section v-else class="landing-hero mx-auto max-w-2xl py-24 text-center">
        <p class="text-xs font-semibold uppercase tracking-widest text-blue-700">Workforce intelligence</p>
        <h1 class="mt-4 text-4xl font-semibold tracking-tight">Every reporting line.<br>One clear picture.</h1>
        <p class="mt-6 leading-relaxed text-slate-600">Explore your organization, understand team costs, and see the people behind the structure.</p>
        <button :disabled="busy" class="mt-8 rounded-xl bg-blue-800 px-6 py-3 font-medium text-white disabled:opacity-50" @click="sample">{{ busy ? 'Preparing your organization…' : 'Explore Giga Corp' }}</button>
        <p class="mt-4 text-xs text-slate-500">40,000 fictional employees · CAD annual salaries · Synthetic sample</p>
        <p class="mt-8 text-sm text-slate-500">Or upload a CSV with employee_id, manager_id, name, salary, and currency columns.</p>
      </section>
      <p v-if="org" class="mt-5 break-words text-xs text-slate-500">{{ datasetName }} · Costs in {{ org.currency }}</p>
    </main>
  </div>
</template>
