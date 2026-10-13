import { computed, ref, watch } from 'vue'

export const ADMIN_PAGE_SIZE = 20

export function paginationPages(page, totalPages) {
  if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1)
  const pages = new Set([1, totalPages, page - 1, page, page + 1])
  if (page <= 3) [2, 3, 4].forEach(value => pages.add(value))
  if (page >= totalPages - 2) [totalPages - 3, totalPages - 2, totalPages - 1].forEach(value => pages.add(value))
  const sorted = [...pages].filter(value => value >= 1 && value <= totalPages).sort((a, b) => a - b)
  return sorted.flatMap((value, i) => i && value - sorted[i - 1] > 1 ? [`ellipsis-${value}`, value] : [value])
}

export function usePagination(items, resetSources = []) {
  const page = ref(1)
  const totalItems = computed(() => items.value.length)
  const totalPages = computed(() => Math.ceil(totalItems.value / ADMIN_PAGE_SIZE))
  const pageItems = computed(() => items.value.slice((page.value - 1) * ADMIN_PAGE_SIZE, page.value * ADMIN_PAGE_SIZE))

  watch(totalPages, total => {
    page.value = Math.min(page.value, Math.max(1, total))
  }, { flush: 'sync' })
  if (resetSources.length) watch(resetSources, () => { page.value = 1 }, { flush: 'sync' })

  return { page, pageItems, totalItems, pageSize: ADMIN_PAGE_SIZE }
}
