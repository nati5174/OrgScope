<script setup lang="ts">
import { computed, ref, shallowRef } from 'vue'
import { type Organization } from '../engine/organization'
import { simulateMove, validateMove, type Scenario } from '../engine/scenario'
import EmployeePicker from './EmployeePicker.vue'
import OrganizationExplorer from './OrganizationExplorer.vue'
const props = defineProps<{ org: Organization }>()
const employeeId = ref(''), destinationId = ref(''), scenario = shallowRef<Scenario | null>(null)
const error = ref(''), previewMode = ref<'original' | 'proposed'>('proposed'), previewChart = ref(false), page = ref(0)
const validation = computed(() => employeeId.value && destinationId.value ? validateMove(props.org, employeeId.value, destinationId.value) : null)
const ready = computed(() => !!employeeId.value && !!destinationId.value && !validation.value)
const stale = computed(() => scenario.value && (employeeId.value !== scenario.value.employeeId || destinationId.value !== scenario.value.destinationId))
const moved = computed(() => scenario.value ? props.org.employees.get(scenario.value.employeeId)! : null)
const affected = computed(() => scenario.value?.affectedIds.slice(page.value * 10, (page.value + 1) * 10) ?? [])
const money = (n: number) => new Intl.NumberFormat('en-CA', { style: props.org.currency === 'XXX' ? 'decimal' : 'currency', currency: props.org.currency, maximumFractionDigits: 0 }).format(n / 100)
const number = (n: number) => n.toLocaleString()
const fields = [
  { key: 'descendantCount', label: 'Descendants', money: false },
  { key: 'nonLeafDescendantCount', label: 'Non-leaf descendants', money: false },
  { key: 'managementCostMinor', label: 'Management cost', money: true },
  { key: 'icCostMinor', label: 'IC cost', money: true },
  { key: 'totalCostMinor', label: 'Total descendant cost', money: true },
] as const
function format(n: number, currency: boolean) { return currency ? money(n) : number(n) }
function delta(n: number, currency: boolean) { return n === 0 ? 'No change' : `${n > 0 ? '+' : '−'}${format(Math.abs(n), currency)}` }
function preview() {
  error.value = ''
  try { scenario.value = simulateMove(props.org, employeeId.value, destinationId.value); page.value = 0; previewMode.value = 'proposed'; previewChart.value = false }
  catch (e) { error.value = e instanceof Error ? e.message : String(e) }
}
function reset() { employeeId.value = ''; destinationId.value = ''; scenario.value = null; error.value = ''; previewChart.value = false; page.value = 0 }
function exportSummary() {
  if (!scenario.value) return
  const s = scenario.value
  const data = { hypothetical: true, currency: props.org.currency, movedEmployee: moved.value,
    originalManagerId: s.originalManagerId, destinationId: s.destinationId,
    affectedEmployees: s.affectedIds.map(id => ({ id, name: props.org.employees.get(id)!.name,
      original: props.org.metrics.get(id), proposed: s.organization.metrics.get(id) })) }
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a'); link.href = url; link.download = 'orgscope-hypothetical-scenario.json'; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>
<template>
  <section class="mt-7" aria-label="Scenario planner">
    <p class="text-xs font-semibold uppercase tracking-widest text-blue-700">Scenario planner</p><h1 class="mt-2 text-3xl font-semibold tracking-tight">Explore a different reporting structure.</h1><p class="mt-3 max-w-3xl text-sm leading-relaxed text-slate-500">Move one employee and their entire team under a different manager. Preview the impact before making any decisions.</p>
    <p class="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">Hypothetical planning only. Your original dataset, explorer, and analytics remain unchanged. Reporting changes redistribute costs; they do not change salaries or create savings.</p>
    <div class="mt-5 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6"><div class="grid gap-6 md:grid-cols-2"><EmployeePicker id="moving-team" v-model="employeeId" :org="org" label="1. Team or employee to move" /><EmployeePicker id="destination-manager" v-model="destinationId" :org="org" label="2. New reporting manager" /></div>
      <p v-if="destinationId && !org.children.get(destinationId)?.length" class="mt-4 text-xs text-slate-500">The destination currently has no reports and would become a manager. Their title and salary will stay the same.</p>
      <p v-if="validation || error" role="alert" class="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800">{{ validation || error }}</p>
      <div class="mt-5 flex flex-wrap items-center gap-3"><button :disabled="!ready" class="rounded-lg bg-blue-800 px-5 py-3 text-sm font-medium text-white" @click="preview">Preview move</button><button class="toolbar text-sm" @click="reset">Reset scenario</button><span class="text-xs text-slate-500">Each preview starts from the original dataset.</span></div>
    </div>
    <p v-if="stale" role="status" class="mt-5 rounded-xl bg-amber-50 p-4 text-sm text-amber-900">Selections changed. Results below show the previous preview. Choose Preview move to update them.</p>
    <template v-if="scenario && moved">
      <div role="status" class="my-5 flex flex-wrap items-center justify-between gap-3 text-sm"><span><strong>{{ moved.name }}</strong> and {{ org.metrics.get(moved.id)!.descendantCount.toLocaleString() }} descendants move together. Salary cost moved: {{ money(org.metrics.get(moved.id)!.totalCostMinor + moved.salaryMinor) }}.</span><button class="toolbar text-xs" @click="exportSummary">Export preview JSON</button></div>
      <div class="grid gap-5 md:grid-cols-2"><section v-for="mode in ['original', 'proposed'] as const" :key="mode" class="rounded-2xl border bg-white p-5" :class="mode === 'proposed' ? 'border-blue-300' : 'border-slate-200'" :aria-label="`${mode} reporting structure`"><h2 class="text-sm font-semibold capitalize">{{ mode }} reporting structure</h2><div class="mt-5 rounded-xl bg-slate-50 p-4"><p class="text-xs text-slate-500">Reports to</p><p class="mt-2 font-semibold">{{ (mode === 'original' ? scenario.originalManagerId : scenario.destinationId) ? org.employees.get((mode === 'original' ? scenario.originalManagerId : scenario.destinationId)!)?.name : 'No manager · organization root' }}</p><p class="mt-1 text-xs text-slate-500">{{ mode === 'original' ? scenario.originalManagerId || 'Root' : scenario.destinationId }}</p></div><div aria-hidden="true" class="ml-8 h-6 border-l-2 border-blue-200"></div><div class="rounded-xl border border-blue-200 p-4"><p class="font-medium">{{ moved.name }}</p><p class="mt-1 text-xs text-slate-500">{{ moved.id }} · {{ (org.metrics.get(moved.id)!.descendantCount + 1).toLocaleString() }} people including team leader</p></div><p class="mt-4 text-xs text-slate-500">The moved team's internal reporting relationships and descendant costs stay the same.</p></section></div>
      <section class="mt-5 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6" aria-label="Scenario metric comparison"><h2 class="text-lg font-semibold">Impact on reporting ancestors</h2><p class="mt-2 text-xs leading-relaxed text-slate-500">Original → proposed, followed by the change. All metrics exclude the employee in that row. Shared ancestors may have no net change. Changes in manager status reclassify salary costs.</p>
        <div class="comparison-scroll mt-5 overflow-x-auto" tabindex="0" role="region" aria-label="Scrollable scenario comparison"><table class="w-full min-w-[1100px] text-left text-xs"><caption class="sr-only">Original and proposed descendant metrics for affected employees</caption><thead class="border-b border-slate-200"><tr><th scope="col" class="p-3">Employee</th><th v-for="field in fields" :key="field.key" scope="col" class="p-3">{{ field.label }}</th></tr></thead><tbody><tr v-for="id in affected" :key="id" class="border-b border-slate-100"><th scope="row" class="p-3 font-medium"><span class="block">{{ org.employees.get(id)?.name }}</span><span class="mt-1 block text-[10px] text-slate-500">{{ org.employees.get(id)?.department || 'Department not provided' }} / {{ org.children.get(id)!.length }} → {{ scenario.organization.children.get(id)!.length }} reports</span></th><td v-for="field in fields" :key="field.key" class="p-3 tabular-nums"><span class="block text-slate-500">{{ format(org.metrics.get(id)![field.key], field.money) }} →</span><strong class="mt-1 block font-medium">{{ format(scenario.organization.metrics.get(id)![field.key], field.money) }}</strong><span class="mt-1 block text-[10px]" :class="scenario.organization.metrics.get(id)![field.key] !== org.metrics.get(id)![field.key] ? 'text-blue-800' : 'text-slate-500'">{{ delta(scenario.organization.metrics.get(id)![field.key] - org.metrics.get(id)![field.key], field.money) }}</span></td></tr></tbody></table></div>
        <div v-if="scenario.affectedIds.length > 10" class="mt-4 flex items-center justify-between text-xs"><button class="toolbar" :disabled="page === 0" @click="page--">Previous ancestors</button><span>{{ page + 1 }} / {{ Math.ceil(scenario.affectedIds.length / 10) }}</span><button class="toolbar" :disabled="(page + 1) * 10 >= scenario.affectedIds.length" @click="page++">Next ancestors</button></div>
        <p class="mt-4 text-xs text-slate-500">{{ scenario.affectedIds.length.toLocaleString() }} ancestor records considered · Preview calculation {{ scenario.calculationMs.toFixed(1) }} ms. No salaries changed.</p>
      </section>
      <div class="mt-5 flex flex-wrap items-center gap-3"><button class="toolbar text-sm" @click="previewChart = !previewChart">{{ previewChart ? 'Hide interactive preview' : 'Open interactive structure preview' }}</button><template v-if="previewChart"><label for="preview-structure" class="text-sm">View</label><select id="preview-structure" v-model="previewMode" class="rounded-lg border border-slate-300 bg-white p-2 text-sm"><option value="original">Original structure</option><option value="proposed">Proposed structure</option></select></template></div>
      <div v-if="previewChart" class="mt-4 rounded-xl border-2 border-dashed border-blue-200 p-3"><p class="text-xs font-medium text-blue-800">{{ previewMode === 'proposed' ? 'Hypothetical proposed organization' : 'Unchanged original organization' }} · structure preview</p><OrganizationExplorer :key="`${scenario.employeeId}-${scenario.destinationId}-${previewMode}`" :org="previewMode === 'proposed' ? scenario.organization : org" :requested-employee="scenario.employeeId" hide-analysis /></div>
    </template>
    <p v-else class="mt-8 text-center text-sm text-slate-500">Select a team and destination to compare a proposed move.</p>
  </section>
</template>

