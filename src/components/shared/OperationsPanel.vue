<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '@/services/apiClient.js'
import TablePagination from '@/components/shared/TablePagination.vue'
import { usePagination } from '@/composables/usePagination.js'
const props = defineProps({ admin: Boolean })
const alerts = ref([])
const equipment = ref([])
const { page: alertPage, pageItems: pagedAlerts, totalItems: alertTotal } = usePagination(alerts)
const { page: equipmentPage, pageItems: pagedEquipment, totalItems: equipmentTotal } = usePagination(equipment)
const error = ref('')
const busy = ref(false)
const showEquipment = ref(false)
const review = ref(null)
const condition = ref('BINH_THUONG')
const note = ref('')
let timer
async function refresh() {
  try { alerts.value = await api.get('/operations/alerts'); error.value = '' }
  catch (err) { error.value = err.message || 'Không tải được cảnh báo.' }
}
async function loadEquipment() {
  showEquipment.value = !showEquipment.value
  if (!showEquipment.value) return
  try { equipment.value = await api.get('/operations/equipment') }
  catch (err) { error.value = err.message }
}
async function save(item) {
  busy.value = true
  try {
    await api.patch(`/operations/equipment/${item.id}`, { quantity: Number(item.quantity), condition: item.condition, note: item.note })
    error.value = ''
  } catch (err) { error.value = err.message }
  finally { busy.value = false }
}
function openReview(alert) {
  review.value = alert
  condition.value = alert.condition || 'BINH_THUONG'
  note.value = alert.note || ''
}
async function confirm() {
  busy.value = true
  try {
    await api.post(`/operations/sessions/${review.value.sessionId}/confirm-return`, { condition: condition.value, note: note.value })
    review.value = null
    await refresh()
  } catch (err) { error.value = err.message }
  finally { busy.value = false }
}
onMounted(() => { refresh(); timer = setInterval(refresh, 30000) })
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <section class="mb-5 rounded-2xl border border-blue-100 bg-white p-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="font-bold text-ink">Cảnh báo và xác nhận trả</h2>
      <div class="flex gap-2">
        <button @click="refresh" class="min-h-11 rounded-xl border border-blue-100 px-3 text-sm text-brand">Làm mới</button>
        <button v-if="admin" @click="loadEquipment" class="min-h-11 rounded-xl border border-blue-100 px-3 text-sm text-brand">Danh mục thiết bị</button>
      </div>
    </div>
    <p v-if="error" role="alert" class="mt-3 text-sm text-red-600">{{ error }}</p>
    <p v-if="!error && !alerts.length" class="mt-3 text-sm text-slate-500">Không có phiếu quá hạn hoặc đang chờ xác nhận trả.</p>
    <ul class="mt-3 space-y-2">
      <li v-for="alert in (admin ? pagedAlerts : alerts)" :key="alert.sessionId" class="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-amber-50 p-3 text-sm">
        <div><b>{{ alert.room }} · Phiếu #{{ alert.sessionId }}</b>
          <p>{{ alert.isOverdue ? 'Quá hạn trả' : 'Chờ kiểm tra trả' }} · Hạn: {{ new Date(alert.dueAt).toLocaleString('vi-VN') }}</p>
          <p v-if="alert.note" class="mt-1 break-words">{{ alert.note }}</p>
        </div>
        <button v-if="admin && alert.needsReview" @click="openReview(alert)" class="min-h-11 rounded-xl bg-brand px-4 text-white">Kiểm tra trả</button>
      </li>
    </ul>
    <TablePagination v-if="admin" v-model:page="alertPage" :total-items="alertTotal" :disabled="busy" label="cảnh báo" />
    <div v-if="review" class="mt-4 space-y-3 rounded-xl border border-blue-100 p-4">
      <p class="font-semibold">Kiểm tra thực tế phiếu #{{ review.sessionId }} trước khi xác nhận.</p>
      <select v-model="condition" class="min-h-11 w-full rounded-lg border border-slate-200 px-3">
        <option value="BINH_THUONG">Đã trả đủ, bình thường</option><option value="HONG_HOC">Đã trả đủ, có hỏng hóc</option><option value="MAT_DO">Thiếu đồ, giữ phiếu chờ xử lý</option>
      </select>
      <textarea v-model="note" maxlength="2000" placeholder="Mô tả thiết bị hỏng/thiếu hoặc ghi chú kiểm tra" class="w-full rounded-lg border border-slate-200 p-3" />
      <button :disabled="busy" @click="confirm" class="min-h-11 rounded-xl bg-brand px-4 text-white disabled:opacity-50">Xác nhận kết quả kiểm tra</button>
      <button :disabled="busy" @click="review = null" class="ml-3 min-h-11 px-3">Hủy</button>
    </div>
    <div v-if="showEquipment" class="mt-4 space-y-3">
      <p class="text-xs text-slate-500">Danh mục hiện tại của phòng; chưa phải danh sách bàn giao theo từng phiếu.</p>
      <div v-for="item in (admin ? pagedEquipment : equipment)" :key="item.id" class="grid gap-2 rounded-xl border border-blue-100 p-3 sm:grid-cols-2">
        <p class="font-semibold sm:col-span-2">{{ item.room }} · {{ item.name }}</p>
        <label class="text-sm">Số lượng hiện có<input :value="item.quantity" readonly type="number" class="mt-1 min-h-11 w-full rounded-lg border border-slate-200 bg-slate-50 px-3" /></label>
        <label class="text-sm">Tình trạng<select v-model="item.condition" class="mt-1 min-h-11 w-full rounded-lg border border-slate-200 px-3"><option value="TOT">Tốt</option><option value="HONG">Hỏng</option><option value="DANG_BAO_TRI">Đang bảo trì</option></select></label>
        <input v-model="item.note" maxlength="255" aria-label="Ghi chú thiết bị" placeholder="Ghi chú" class="min-h-11 rounded-lg border border-slate-200 px-3" />
        <button :disabled="busy" @click="save(item)" class="min-h-11 rounded-xl bg-brand px-4 text-white disabled:opacity-50">Lưu thiết bị</button>
      </div>
      <TablePagination v-if="admin" v-model:page="equipmentPage" :total-items="equipmentTotal" :disabled="busy" label="thiết bị" />
    </div>
  </section>
</template>
