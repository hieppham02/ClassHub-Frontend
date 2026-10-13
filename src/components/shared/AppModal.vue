<script setup>
import { useId } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  size: { type: String, default: 'sm' },
  layer: { type: String, default: 'normal' },
  busy: Boolean
})
const emit = defineEmits(['close'])
const titleId = useId()
const widths = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-lg' }
const layers = { normal: 'z-[70]', nested: 'z-[80]', cabinet: 'z-[60]' }
function close() {
  if (!props.busy) emit('close')
}
</script>

<template>
  <div class="app-modal fixed inset-0 flex items-center justify-center bg-ink/40 p-4 sm:p-5 backdrop-blur-sm" :class="layers[layer] || layers.normal" @click.self="close">
    <section role="dialog" aria-modal="true" :aria-labelledby="titleId" :aria-busy="busy"
      class="flex max-h-[calc(100dvh-2rem)] w-full flex-col overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-2xl"
      :class="widths[size] || widths.sm">
      <header class="flex shrink-0 items-center justify-between gap-4 border-b border-blue-50 bg-blue-50/60 p-5 text-ink">
        <div class="min-w-0">
          <h2 :id="titleId" class="text-base font-bold leading-snug tracking-tight">{{ title }}</h2>
          <slot name="subtitle" />
        </div>
        <button type="button" aria-label="Đóng hộp thoại" :disabled="busy" @click="close"
          class="flex size-8 shrink-0 items-center justify-center rounded-full bg-blue-100/60 text-slate-600 transition hover:bg-blue-200/60 disabled:cursor-not-allowed disabled:opacity-50">
          <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </header>
      <div class="min-h-0 overflow-y-auto overscroll-contain p-5 sm:p-6"><slot /></div>
      <footer v-if="$slots.footer" class="flex shrink-0 gap-3 border-t border-blue-50 bg-slate-50 p-4"><slot name="footer" /></footer>
    </section>
  </div>
</template>
