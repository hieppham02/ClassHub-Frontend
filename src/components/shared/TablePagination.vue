<script setup>
import { computed } from 'vue'
import { ADMIN_PAGE_SIZE, paginationPages } from '@/composables/usePagination.js'

const props = defineProps({
  page: { type: Number, required: true },
  totalItems: { type: Number, required: true },
  pageSize: { type: Number, default: ADMIN_PAGE_SIZE },
  disabled: Boolean,
  compact: Boolean,
  label: { type: String, default: 'bản ghi' }
})
const emit = defineEmits(['update:page'])
const totalPages = computed(() => Math.ceil(props.totalItems / props.pageSize))
const pages = computed(() => paginationPages(props.page, totalPages.value))
const start = computed(() => props.totalItems ? (props.page - 1) * props.pageSize + 1 : 0)
const end = computed(() => Math.min(props.page * props.pageSize, props.totalItems))

function goToPage(page) {
  if (!props.disabled && page >= 1 && page <= totalPages.value && page !== props.page) emit('update:page', page)
}
</script>

<template>
  <div v-if="totalItems > 0" class="flex gap-4 border-t border-blue-100 bg-slate-50/60 px-4 py-4 sm:px-5"
    :class="compact ? 'items-center justify-center' : 'flex-col sm:flex-row sm:items-center sm:justify-between'">
    <p v-if="!compact" class="text-xs text-slate-500" aria-live="polite">
      Hiển thị <span class="font-bold text-slate-700">{{ start }}–{{ end }}</span>
      trong <span class="font-bold text-slate-700">{{ totalItems }}</span> {{ label }}
      · {{ pageSize }} dòng/trang
    </p>
    <nav aria-label="Phân trang" class="flex flex-wrap items-center gap-1.5" :class="compact ? 'justify-center' : ''">
      <button type="button" :disabled="disabled || page <= 1" @click="goToPage(page - 1)"
        class="min-h-10 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 disabled:cursor-not-allowed disabled:opacity-40">Trước</button>
      <template v-for="value in pages" :key="value">
        <span v-if="typeof value === 'string'" class="px-1 text-slate-400" aria-hidden="true">…</span>
        <button v-else type="button" :disabled="disabled" :aria-label="`Trang ${value}`" :aria-current="value === page ? 'page' : undefined"
          :class="value === page ? 'border-brand bg-brand text-white' : 'border-slate-200 bg-white text-slate-600 hover:border-brand hover:text-brand'"
          class="min-h-10 min-w-10 rounded-lg border px-2 text-xs font-bold disabled:opacity-40" @click="goToPage(value)">{{ value }}</button>
      </template>
      <button type="button" :disabled="disabled || page >= totalPages" @click="goToPage(page + 1)"
        class="min-h-10 rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-600 disabled:cursor-not-allowed disabled:opacity-40">Sau</button>
    </nav>
  </div>
</template>
