<script setup lang="ts">
import type { Employee } from '../engine/organization'
defineProps<{ employee: Employee; reports: number; descendants: number; nonLeafDescendants: number; selected: boolean; expanded: boolean; page: number; pageCount: number; isRoot: boolean }>()
const emit = defineEmits<{ select: []; toggle: []; page: [delta: number]; focus: [] }>()
function selectSurface(event: MouseEvent) {
  // The native main button and footer controls already own their actions.
  // Select once for the remaining card surface, including stats and whitespace.
  if (!(event.target as Element).closest('button')) emit('select')
}
</script>
<template>
  <article class="employee-card" :class="{ 'is-selected': selected, 'is-root': isRoot }" :data-card="employee.id" @click="selectSurface">
    <button class="employee-card-main" :data-employee="employee.id" :aria-pressed="selected" :aria-description="`Employee ID ${employee.id}`" @click="$emit('select')">
      <span class="employee-avatar" aria-hidden="true">{{ employee.name.split(' ').map(n => n[0]).slice(0, 2).join('') }}</span>
      <span class="min-w-0"><span class="employee-card-name" :title="employee.name">{{ employee.name }}</span><span class="employee-card-title" :title="[employee.title, employee.department].filter(Boolean).join(' / ')">{{ employee.title || 'Title not provided' }}<template v-if="employee.department"> / {{ employee.department }}</template></span></span>
      <span v-if="isRoot" class="root-dot" title="Organization root" aria-label="Organization root"></span>
    </button>
    <div class="employee-card-stats"><span title="Descendants with direct reports">{{ nonLeafDescendants.toLocaleString() }} non-leaf</span><span>{{ descendants.toLocaleString() }} descendants</span></div>
    <div class="employee-card-footer"><button v-if="reports" :aria-expanded="expanded" :aria-label="`${expanded ? 'Collapse' : 'Expand'} reports for ${employee.id}`" @click="$emit('toggle')"><span aria-hidden="true">{{ expanded ? '−' : '+' }}</span> {{ expanded ? 'Collapse' : 'Expand' }}</button><span v-else class="text-slate-400">Individual contributor</span><div v-if="expanded && pageCount > 1" class="card-pager"><button :disabled="page === 0" :aria-label="`Previous reports for ${employee.id}`" @click="$emit('page', -1)">‹</button><span>{{ page + 1 }}/{{ pageCount }}</span><button :disabled="page + 1 >= pageCount" :aria-label="`Next reports for ${employee.id}`" @click="$emit('page', 1)">›</button></div><button v-else class="card-focus" :aria-label="`Focus on ${employee.name}`" @click="$emit('focus')">Focus</button></div>
  </article>
</template>
