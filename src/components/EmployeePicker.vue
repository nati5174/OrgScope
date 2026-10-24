<script setup lang="ts">
import { computed, ref } from 'vue'
import { searchEmployees, type Organization } from '../engine/organization'
const props = defineProps<{ org: Organization; id: string; label: string; modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [id: string] }>()
const query = ref('')
const matches = computed(() => searchEmployees(props.org, query.value, 20))
const employee = computed(() => props.org.employees.get(props.modelValue))
function choose(id: string) { emit('update:modelValue', id); query.value = '' }
</script>
<template>
  <div class="relative min-w-0"><label :for="id" class="text-sm font-semibold">{{ label }}</label><input :id="id" v-model="query" placeholder="Search name or employee ID" class="mt-3 w-full rounded-xl border border-slate-300 bg-white p-3 text-sm" @keydown.escape="query = ''"><div v-if="query.trim()" class="absolute left-0 right-0 z-40 mt-1 max-h-64 overflow-auto rounded-xl border border-slate-200 bg-white p-2 shadow-xl"><p v-if="!matches.length" class="p-3 text-xs text-slate-500">No employees found</p><button v-for="match in matches" :key="match.id" :aria-label="`Select ${match.name} (${match.id})`" class="block w-full rounded-lg p-3 text-left text-sm hover:bg-blue-50" @click="choose(match.id)">{{ match.name }}<span class="mt-1 block text-xs text-slate-500">{{ match.id }} · {{ match.department }}</span></button></div><div class="mt-3 rounded-lg bg-slate-50 p-3 text-sm"><template v-if="employee"><p class="font-medium">{{ employee.name }}</p><p class="mt-1 text-xs text-slate-500">{{ employee.id }} · {{ employee.title || 'Title not provided' }}</p></template><p v-else class="text-slate-500">No employee selected</p></div></div>
</template>
