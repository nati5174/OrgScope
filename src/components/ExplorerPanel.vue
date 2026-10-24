<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
const props = defineProps<{ open: boolean; desktop: boolean; side: 'left' | 'right'; label: string }>()
const emit = defineEmits<{ close: [] }>()
const panel = ref<HTMLElement>()
async function sync() {
  await nextTick()
  if (panel.value instanceof HTMLDialogElement) {
    if (props.open && !panel.value.open) panel.value.showModal()
    if (!props.open && panel.value.open) panel.value.close()
  }
}
watch(() => [props.open, props.desktop], sync)
onMounted(sync)
onBeforeUnmount(() => { if (panel.value instanceof HTMLDialogElement && panel.value.open) panel.value.close() })
</script>
<template>
  <component :is="desktop ? 'aside' : 'dialog'" ref="panel" class="explorer-panel" :class="[`panel-${side}`, { 'desktop-panel': desktop, 'panel-hidden': desktop && !open }]" :aria-label="label" @cancel.prevent="emit('close')" @click="(event: MouseEvent) => { if (event.target === panel && !desktop) emit('close') }"><div class="panel-content"><slot /></div></component>
</template>
