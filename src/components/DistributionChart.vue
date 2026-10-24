<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ title: string; description: string; buckets: { label: string; count: number }[]; color?: string }>()
const maximum = computed(() => Math.max(1, ...props.buckets.map(b => b.count)))
</script>
<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6" :aria-label="title">
    <h2 class="text-base font-semibold">{{ title }}</h2><p class="mt-2 text-xs leading-relaxed text-slate-500">{{ description }}</p>
    <p v-if="!buckets.some(b => b.count)" class="mt-6 text-sm text-slate-500">No managers in this scope.</p>
    <ul v-else class="mt-6 space-y-3"><li v-for="bucket in buckets" :key="bucket.label" class="grid grid-cols-[minmax(80px,1fr)_2fr_48px] items-center gap-3 text-xs"><span class="text-slate-600">{{ bucket.label }}</span><div class="h-5 overflow-hidden rounded bg-slate-100" aria-hidden="true"><div class="h-full rounded" :class="color || 'bg-blue-600'" :style="{ width: `${bucket.count / maximum * 100}%` }"></div></div><span class="text-right font-medium tabular-nums">{{ bucket.count.toLocaleString() }}</span></li></ul>
  </section>
</template>
