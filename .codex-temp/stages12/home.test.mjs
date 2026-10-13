import { readFileSync } from 'node:fs'
import vm from 'node:vm'
import assert from 'node:assert/strict'
const source = readFileSync('src/views/client/HomeView.vue', 'utf8').split('<script setup>')[1].split('</script>')[0]
  .replace(/^import .*$/gm, '')
const calls = []
let failReport = false
const context = vm.createContext({
  ref: value => ({ value }), computed: fn => ({ get value() { return fn() } }),
  watch() {}, onMounted() {}, onUnmounted() {}, nextTick: async () => {},
  window: { location: { pathname: '/' } }, console, Date,
  setTimeout() {}, setInterval() {}, clearInterval() {},
  api: {
    get: async path => path.includes('slots') ? [{ id: 9, name: 'Buổi sáng', start: '06:45', end: '09:15' }] : [],
    put: async (path, body) => { calls.push({ path, body }); if (failReport && path.includes('return-report')) throw new Error('report failed') }
  }
})
vm.runInContext(source + '\nglobalThis.test = { fetchSlots, selectedSlotId, slot, danhSachCaHoc, returnRoom, activeBooking, returnCondition, returnNote };', context)
const t = context.test
await t.fetchSlots()
t.slot.value = t.danhSachCaHoc.value[0]
assert.equal(t.selectedSlotId.value, 9, 'Use database ca_id rather than label digits or index')
t.activeBooking.value = { id: 12, room: 'A1', status: 'ACTIVE' }
t.returnCondition.value = 'MAT_DO'; t.returnNote.value = 'Thiếu micro'
failReport = true
await t.returnRoom()
assert.equal(calls.length, 1, 'Failed report must not send lock request')
calls.length = 0; failReport = false
t.activeBooking.value = { id: 12, room: 'A1', status: 'ACTIVE' }
await t.returnRoom()
assert.equal(calls.length, 2)
assert.ok(calls[0].path.includes('return-report'))
assert.equal(calls[0].body.condition, 'MAT_DO')
assert.ok(calls[1].path.includes('return-room'))
calls.length = 0
t.activeBooking.value = { id: 12, room: 'A1', status: 'RETURNING' }
await t.returnRoom()
assert.equal(calls.length, 1, 'Retry RETURNING only resends lock')
assert.ok(calls[0].path.includes('return-room'))
calls.length = 0
t.activeBooking.value = { id: 12, room: 'A1', status: 'PENDING' }
await t.returnRoom()
assert.equal(calls.length, 0, 'Pending cannot return')
console.log('Passed: slot ID, failed report, return ordering, retry and pending guards.')
