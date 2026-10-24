<script setup lang="ts">
import { computed } from 'vue'
import { managementCostRatio, type Organization } from '../engine/organization'
const props = defineProps<{ org: Organization; id: string; hideAnalysis?: boolean; depth?: number }>()
defineEmits<{ focus: [id: string]; select: [id: string]; analyze: [id: string]; close: [] }>()
const employee = computed(() => props.org.employees.get(props.id)!)
const metrics = computed(() => props.org.metrics.get(props.id)!)
const money = (v: number) => new Intl.NumberFormat('en-CA', { style: 'currency', currency: props.org.currency, maximumFractionDigits: 0 }).format(v / 100)
const costs = computed(() => [
  { label: 'Management cost', value: money(metrics.value.managementCostMinor), help: 'Salaries of descendants who have direct reports.' },
  { label: 'IC cost', value: money(metrics.value.icCostMinor), help: 'Salaries of descendants who have no direct reports.' },
  { label: 'Total descendant cost', value: money(metrics.value.totalCostMinor), help: 'Management cost plus IC cost. Excludes this employee.' },
  { label: 'Management cost ratio', value: managementCostRatio(metrics.value)?.toFixed(2) ?? 'N/A', help: 'IC salary cost divided by management salary cost. N/A when management cost is zero.' },
])
const managerShare = computed(() => metrics.value.totalCostMinor ? metrics.value.managementCostMinor / metrics.value.totalCostMinor * 100 : 0)
</script>
<template>
  <aside aria-label="Employee details" class="employee-inspector">
    <div class="panel-heading"><h2>Employee inspector</h2><button class="icon-button" aria-label="Close employee inspector" @click="$emit('close')">×</button></div>
    <div class="inspector-body">
      <div class="inspector-profile"><div class="inspector-avatar" aria-hidden="true">{{ employee.name.split(' ').map(n => n[0]).slice(0, 2).join('') }}</div><span class="employee-kind">{{ employee.managerId === null ? 'Organization root' : org.children.get(id)!.length ? 'People manager' : 'Individual contributor' }}</span><h2>{{ employee.name }}</h2><p>{{ employee.title || 'Title not provided' }}</p><small>{{ employee.id }}<template v-if="employee.department"> · {{ employee.department }}</template></small></div>
      <div class="inspector-actions"><button class="primary-button" @click="$emit('focus', id)">Focus here</button><button v-if="!hideAnalysis" class="secondary-button" @click="$emit('analyze', id)">Analyze this team</button></div>
      <section class="inspector-section"><h3>Reporting structure</h3><button v-if="employee.managerId" class="manager-link" @click="$emit('select', employee.managerId)"><span>Reports to</span><strong>{{ org.employees.get(employee.managerId)!.name }} ↗</strong></button><p v-else class="inspector-note">Top of this organization</p><dl class="inspector-org-metrics"><div><dt>Direct reports</dt><dd>{{ org.children.get(id)!.length.toLocaleString() }}</dd></div><div><dt>Total descendants</dt><dd>{{ metrics.descendantCount.toLocaleString() }}</dd></div><div><dt title="Descendants with at least one direct report">Non-leaf descendants</dt><dd>{{ metrics.nonLeafDescendantCount.toLocaleString() }}</dd></div><div v-if="depth !== undefined"><dt title="Reporting edges from the organization root; root is level 0">Reporting level</dt><dd>{{ depth }}</dd></div></dl></section>
      <section class="inspector-section"><h3>Workforce costs <span>{{ org.currency }} / year</span></h3><p class="inspector-note">Descendant-only costs exclude {{ employee.name }}.</p><div v-if="metrics.totalCostMinor" class="inspector-cost-bar" aria-hidden="true"><span :style="{ width: `${managerShare}%` }"></span></div><div v-if="metrics.totalCostMinor" class="cost-legend"><span>● Managers {{ managerShare.toFixed(1) }}%</span><span>● ICs {{ (100 - managerShare).toFixed(1) }}%</span></div><dl class="inspector-costs"><div v-for="cost in costs" :key="cost.label"><dt :title="cost.help">{{ cost.label }}</dt><dd>{{ cost.value }}</dd></div></dl><details class="metric-help"><summary>How are costs calculated?</summary><p v-for="cost in costs" :key="cost.label"><strong>{{ cost.label }}:</strong> {{ cost.help }}</p></details></section>
      <section class="inspector-section"><h3>Employee information</h3><dl class="inspector-org-metrics"><div><dt>Annual salary</dt><dd>{{ money(employee.salaryMinor) }}</dd></div><div v-if="employee.location"><dt>Location</dt><dd>{{ employee.location }}</dd></div></dl></section>
    </div>
  </aside>
</template>
