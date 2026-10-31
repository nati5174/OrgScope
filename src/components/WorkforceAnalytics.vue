<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { analyzeWorkforce } from '../engine/analytics'
import { ancestorPath } from '../engine/explorer'
import { searchEmployees, type Organization } from '../engine/organization'
import DistributionChart from './DistributionChart.vue'
const props = defineProps<{ org: Organization; scope: string | null }>()
const emit = defineEmits<{ scope: [id: string | null]; explore: [id: string] }>()
const query = ref(''), page = ref(0), exact = ref(false), sort = ref<'cost' | 'headcount' | 'management'>('cost')
// A replacement dataset can keep the same null scope but have fewer branches.
watch([() => props.org, () => props.scope], () => { page.value = 0; query.value = '' })
const matches = computed(() => searchEmployees(props.org, query.value, 20))
const summary = computed(() => analyzeWorkforce(props.org, props.scope))
const leader = computed(() => props.scope ? props.org.employees.get(props.scope) : null)
const ancestors = computed(() => props.scope ? ancestorPath(props.org, props.scope) : [])
const breadcrumbs = computed(() => ancestors.value.slice(-4))
const orderedBranches = computed(() => [...summary.value.branches].sort((a, b) => {
  const value = (branch: typeof a) => sort.value === 'headcount' ? branch.headcount : sort.value === 'management' ? (branch.totalCostMinor ? branch.managementCostMinor / branch.totalCostMinor : 0) : branch.totalCostMinor
  return value(b) - value(a) || a.id.localeCompare(b.id)
}))
const branches = computed(() => orderedBranches.value.slice(page.value * 10, (page.value + 1) * 10))
watch(sort, () => { page.value = 0 })
const money = (n: number, compact = false) => new Intl.NumberFormat('en-CA', { style: props.org.currency === 'XXX' ? 'decimal' : 'currency', currency: props.org.currency, minimumFractionDigits: exact.value ? 2 : 0, maximumFractionDigits: exact.value ? 2 : compact ? 1 : 0, notation: compact && !exact.value ? 'compact' : 'standard' }).format(n / 100)
const percent = (n: number, total: number) => total ? `${(100 * n / total).toFixed(1)}%` : 'N/A'
const salaryBuckets = computed(() => summary.value.salaryBuckets.map(b => ({ count: b.count,
  label: b.minMinor === b.maxMinor ? money(b.minMinor, true) : `${money(b.minMinor, true)} – ${money(b.maxMinor, true)}` })))
const cards = computed(() => [
  { label: 'Team headcount', value: summary.value.headcount.toLocaleString(), note: `${summary.value.managers.toLocaleString()} managers · ${summary.value.ics.toLocaleString()} ICs` },
  { label: 'Annual salary cost', value: money(summary.value.totalCostMinor, true), note: money(summary.value.totalCostMinor) },
  { label: 'Average annual salary', value: money(summary.value.averageSalaryMinor), note: `Range ${money(summary.value.minSalaryMinor, true)} – ${money(summary.value.maxSalaryMinor, true)}` },
  { label: 'Average span of control', value: summary.value.averageSpan?.toFixed(1) ?? 'N/A', note: 'Direct reports per manager; ICs excluded' },
])
function changeScope(id: string | null) { query.value = ''; emit('scope', id) }
</script>
<template>
  <section class="mt-7" aria-label="Workforce analytics">
    <div class="flex flex-wrap items-end justify-between gap-5"><div><p class="text-xs font-semibold uppercase tracking-widest text-blue-700">Workforce analytics</p><h1 class="mt-2 text-3xl font-semibold tracking-tight">See where your organization invests.</h1><p class="mt-2 text-sm text-slate-500">Compare reporting branches, understand salary costs, and examine management structure.</p></div>
      <div class="relative w-full sm:w-80"><label for="analytics-search" class="sr-only">Choose analytics team by name or ID</label><input id="analytics-search" v-model="query" placeholder="Choose a team by name or ID" class="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm" @keydown.escape="query = ''"><div v-if="query.trim()" class="absolute right-0 z-30 mt-2 max-h-80 w-full overflow-auto rounded-xl border border-slate-200 bg-white p-2 shadow-xl"><p class="px-3 py-2 text-xs text-slate-500">{{ matches.length ? 'Select an employee and their reporting subtree' : 'No employees found' }}</p><button v-for="match in matches" :key="match.id" :aria-label="`Analyze ${match.name} (${match.id})`" class="block w-full rounded-lg p-3 text-left text-sm hover:bg-blue-50" @click="changeScope(match.id)">{{ match.name }}<span class="mt-1 block text-xs text-slate-500">{{ match.title || 'Title not provided' }}<template v-if="match.department"> / {{ match.department }}</template></span></button></div></div>
    </div>
    <div class="my-6 rounded-xl border border-blue-100 bg-blue-50/60 p-4">
      <div class="flex flex-wrap items-center justify-between gap-3"><nav aria-label="Analytics scope breadcrumbs" class="flex min-w-0 flex-wrap items-center gap-2 text-xs"><button class="font-medium text-blue-800 underline" @click="changeScope(null)">Entire organization</button><span v-if="ancestors.length > 4">/ …</span><template v-for="id in breadcrumbs" :key="id"><span>/</span><button :aria-current="id === scope ? 'location' : undefined" class="max-w-44 truncate text-blue-800 underline" @click="changeScope(id)">{{ org.employees.get(id)?.name }}</button></template></nav><button v-if="scope" class="toolbar text-xs" @click="emit('explore', scope)">Explore this team →</button></div>
      <p class="mt-3 text-sm font-medium">{{ leader ? `${leader.name} and their reporting subtree` : 'All employees across every root' }}</p><p class="mt-1 text-xs text-slate-600">All analytics include the selected leader's salary and headcount. Managers are employees with direct reports. Salaries are annual base pay in {{ org.currency === 'XXX' ? 'unspecified currency' : org.currency }}.</p>
    </div>
    <label class="mb-4 flex items-center gap-2 text-xs"><input v-model="exact" type="checkbox">Show exact salary amounts</label>
    <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><section v-for="card in cards" :key="card.label" class="rounded-2xl border border-slate-200 bg-white p-5" :aria-label="card.label"><h2 class="text-xs text-slate-500">{{ card.label }}</h2><p class="mt-3 text-3xl font-semibold tracking-tight tabular-nums">{{ card.value }}</p><p class="mt-3 text-xs text-slate-500">{{ card.note }}</p></section></div>
    <div class="mt-5 grid items-start gap-5 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
      <section class="min-w-0 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6" aria-label="Branch cost concentration">
        <h2 class="text-base font-semibold">Where is salary cost concentrated?</h2><p class="mt-2 text-xs leading-relaxed text-slate-500">Compare disjoint reporting branches by salary cost, headcount, or management cost share. Select a branch to drill in. Each branch includes its leader.</p>
        <label class="mt-4 flex flex-wrap items-center gap-2 text-xs">Order branches by<select v-model="sort" class="rounded border border-slate-300 p-2"><option value="cost">Annual salary cost</option><option value="headcount">Headcount</option><option value="management">Management cost share</option></select></label>
        <p v-if="!summary.branches.length" class="my-8 text-sm text-slate-500">This employee has no direct reports. Their salary is the entire scope cost.</p>
        <div v-else class="mt-5 overflow-x-auto"><table class="w-full min-w-[460px] text-left text-xs"><caption class="sr-only">Reporting branch cost and headcount comparisons</caption><thead class="border-b border-slate-200 text-slate-500"><tr><th scope="col" class="pb-3 font-medium">Reporting branch</th><th scope="col" class="pb-3 text-right font-medium">People</th><th scope="col" class="pb-3 text-right font-medium">Annual cost</th><th scope="col" class="pb-3 text-right font-medium">Manager cost</th></tr></thead><tbody><tr v-for="branch in branches" :key="branch.id" :data-branch="branch.id" class="border-b border-slate-100"><th scope="row" class="py-4 pr-4 font-normal"><button class="w-full text-left text-blue-800" @click="changeScope(branch.id)"><span class="block max-w-56 truncate font-semibold">{{ org.employees.get(branch.id)?.name }}</span><span class="mt-1 block text-[10px] text-slate-500">{{ org.employees.get(branch.id)?.title || 'Title not provided' }} / {{ org.employees.get(branch.id)?.department || 'Department not provided' }}</span><span aria-hidden="true" class="mt-2 block h-1.5 w-full rounded bg-slate-100"><span class="block h-1.5 rounded bg-blue-600" :style="{ width: `${summary.totalCostMinor ? branch.totalCostMinor / summary.totalCostMinor * 100 : 0}%` }"></span></span></button><button class="mt-2 text-xs text-blue-800 underline" :aria-label="`Explore ${org.employees.get(branch.id)?.name} in chart`" @click="emit('explore', branch.id)">Explore in chart</button></th><td class="text-right tabular-nums">{{ branch.headcount.toLocaleString() }}</td><td class="pl-3 text-right tabular-nums"><span :title="money(branch.totalCostMinor)">{{ money(branch.totalCostMinor, true) }}</span><span class="mt-1 block text-[10px] text-slate-500">{{ percent(branch.totalCostMinor, summary.totalCostMinor) }} of scope</span></td><td class="pl-3 text-right tabular-nums">{{ percent(branch.managementCostMinor, branch.totalCostMinor) }}</td></tr></tbody></table></div>
        <div v-if="summary.branches.length > 10" class="mt-4 flex items-center justify-between text-xs"><button class="toolbar" :disabled="page === 0" @click="page--">Previous branches</button><span>Page {{ page + 1 }} / {{ Math.ceil(summary.branches.length / 10) }}</span><button class="toolbar" :disabled="(page + 1) * 10 >= summary.branches.length" @click="page++">Next branches</button></div>
        <p class="mt-5 text-xs leading-relaxed text-slate-500">Branch salaries + scope leader salary ({{ money(summary.leaderCostMinor) }}) = {{ money(summary.totalCostMinor) }}. For a forest with multiple roots, branches are the roots and no leader is added.</p>
      </section>
      <section class="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6" aria-label="Management and IC breakdown">
        <h2 class="text-base font-semibold">Management & individual contributors</h2><p class="mt-2 text-xs leading-relaxed text-slate-500">Compare the share of people with the share of salary spending. These are descriptive measures, not staffing targets.</p>
        <div class="mt-7 flex gap-5 text-xs"><span><span class="mr-2 inline-block h-2 w-2 rounded bg-blue-700"></span>Managers</span><span><span class="mr-2 inline-block h-2 w-2 rounded bg-sky-300"></span>ICs</span></div>
        <div v-for="row in [{ label: 'Headcount', manager: summary.managers, ic: summary.ics, total: summary.headcount }, { label: 'Salary cost', manager: summary.managementCostMinor, ic: summary.icCostMinor, total: summary.totalCostMinor }]" :key="row.label" class="mt-6"><div class="flex justify-between text-xs"><span class="font-medium">{{ row.label }}</span><span class="text-slate-500">{{ percent(row.manager, row.total) }} managers</span></div><div aria-hidden="true" class="mt-3 flex h-5 overflow-hidden rounded bg-slate-100"><div class="bg-blue-700" :style="{ width: `${row.total ? row.manager / row.total * 100 : 0}%` }"></div><div class="bg-sky-300" :style="{ width: `${row.total ? row.ic / row.total * 100 : 0}%` }"></div></div></div>
        <dl class="mt-6 space-y-3 border-t border-slate-100 pt-5 text-xs"><div class="flex justify-between gap-3"><dt>Manager salaries</dt><dd>{{ money(summary.managementCostMinor) }}</dd></div><div class="flex justify-between gap-3"><dt>IC salaries</dt><dd>{{ money(summary.icCostMinor) }}</dd></div><div class="flex justify-between gap-3"><dt>IC cost ÷ manager cost</dt><dd>{{ summary.managementCostMinor ? (summary.icCostMinor / summary.managementCostMinor).toFixed(2) : 'N/A' }}</dd></div><div class="flex justify-between gap-3"><dt>IC headcount per manager</dt><dd>{{ summary.managers ? (summary.ics / summary.managers).toFixed(2) : 'N/A' }}</dd></div></dl>
      </section>
    </div>
    <div class="mt-5 grid gap-5 lg:grid-cols-3">
      <DistributionChart title="Salary distribution" description="Employee counts in equal-width salary bands. Rounded range labels; exact boundaries are listed below." :buckets="salaryBuckets" />
      <DistributionChart title="Reporting depth" :description="`Level 0 is the scope leader (or each root). Deepest level: ${summary.maxDepth}; management layers: ${summary.managementLayers}. Levels 10 and above are grouped.`" :buckets="summary.depthBuckets" color="bg-sky-500" />
      <DistributionChart title="Span of control" description="Number of managers in each direct-report band. Individual contributors are excluded." :buckets="summary.spanBuckets" color="bg-slate-500" />
    </div>
    <details class="mt-5 rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600"><summary class="cursor-pointer font-medium">Metric definitions & exact salary bands</summary><p class="mt-3 leading-relaxed">Headcount and costs include every person in the scope once. Average span = direct reporting relationships ÷ managers. Management layers = distinct relative depths containing managers. Cost shares are N/A when all salaries are zero. Manager classification uses the complete reporting structure.</p><ul class="mt-3 space-y-1"><li v-for="(bucket, index) in summary.salaryBuckets" :key="index">Band {{ index + 1 }}: {{ (bucket.minMinor / 100).toFixed(2) }}–{{ (bucket.maxMinor / 100).toFixed(2) }} {{ org.currency === 'XXX' ? 'unspecified currency' : org.currency }} · {{ bucket.count.toLocaleString() }} employees</li></ul></details>
  </section>
</template>
