import assert from 'node:assert/strict'
import { computed, effectScope, ref } from 'vue'
import { ADMIN_PAGE_SIZE, paginationPages, usePagination } from '../src/composables/usePagination.js'

const scope = effectScope()
scope.run(() => {
  const records = ref(Array.from({ length: 56 }, (_, i) => ({ id: i + 1, role: i < 41 ? 'student' : 'other' })))
  const filter = ref('all')
  const visible = computed(() => records.value.filter(item => filter.value === 'all' || item.role === filter.value))
  const paging = usePagination(visible, [filter])
  assert.equal(ADMIN_PAGE_SIZE, 20)
  assert.equal(paging.pageItems.value.length, 20)
  paging.page.value = 2
  assert.deepEqual(paging.pageItems.value.map(item => item.id), Array.from({ length: 20 }, (_, i) => i + 21))
  paging.page.value = 3
  assert.equal(paging.pageItems.value.length, 16)
  filter.value = 'other'
  assert.equal(paging.page.value, 1)
  assert.equal(paging.pageItems.value.length, 15)
  filter.value = 'all'
  paging.page.value = 3
  records.value = records.value.slice(0, 40)
  assert.equal(paging.page.value, 2)
  assert.equal(paging.pageItems.value.length, 20)
  records.value = []
  assert.equal(paging.page.value, 1)
  assert.equal(paging.totalItems.value, 0)
  assert.deepEqual(paging.pageItems.value, [])

  // Realtime updates keep the selected page when it remains valid.
  records.value = Array.from({ length: 45 }, (_, i) => ({ id: i, role: 'student' }))
  paging.page.value = 2
  records.value[20].role = 'other'
  assert.equal(paging.page.value, 2)
  assert.equal(paging.pageItems.value[0].role, 'other')

  // Pagination never truncates the source used by statistics or selectors.
  assert.equal(records.value.length, 45)
  assert.equal(paging.pageItems.value.length, 20)
  const other = usePagination(ref(Array.from({ length: 21 }, (_, i) => i)))
  other.page.value = 2
  assert.equal(paging.page.value, 2)
  paging.page.value = 1
  assert.equal(other.page.value, 2)
})
scope.stop()
assert.deepEqual(paginationPages(1, 0), [])
assert.deepEqual(paginationPages(2, 3), [1, 2, 3])
assert.deepEqual(paginationPages(80, 158), [1, 'ellipsis-79', 79, 80, 81, 'ellipsis-158', 158])
assert.deepEqual(paginationPages(1, 10), [1, 2, 3, 4, 'ellipsis-10', 10])
assert.deepEqual(paginationPages(10, 10), [1, 'ellipsis-7', 7, 8, 9, 10])
console.log('PASS: 20 rows/page, filters, final-page deletion, empty lists, realtime updates, independent lists and compact navigation.')
