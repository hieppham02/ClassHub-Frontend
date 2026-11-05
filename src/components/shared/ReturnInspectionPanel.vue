<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api } from '@/services/apiClient.js'
import RfidSummary from './RfidSummary.vue'
const props = defineProps({ sessionId: { type: Number, required: true }, admin: Boolean })
const emit = defineEmits(['confirmed'])
const evidence = ref(null), error = ref(''), busy = ref(false), loading = ref(false)
const condition = ref('BINH_THUONG'), note = ref(''), counts = ref({})
const acknowledged = ref(false)
const analysisItems = computed(() => Array.isArray(inspection.value?.analysis?.items) ? inspection.value.analysis.items : [])
const boxes = computed(() => analysisItems.value.flatMap(item => Array.isArray(item.detections) ? item.detections : []).filter(d =>
  Array.isArray(d.box) && d.box.length === 4 && d.box.every(Number.isFinite) && Number.isFinite(d.confidence)))
function observed(id) { return analysisItems.value.find(item => item.snapshotId === id)?.observed }
let timer, stopped = false
const inspection = computed(() => evidence.value?.inspection)
const complete = computed(() => (evidence.value?.expected || []).length > 0 &&
  evidence.value.expected.every(item => Number(counts.value[item.snapshotId]) === item.quantity))
const canConfirm = computed(() => props.admin && evidence.value?.canCapture && inspection.value &&
  acknowledged.value && note.value.trim() && (condition.value === 'MAT_DO' || complete.value))
async function load() {
  if (loading.value || busy.value) return
  loading.value = true
  try {
    const result = await api.get(`/operations/sessions/${props.sessionId}/inspection`)
    if (stopped) return
    if (result.inspection?.id !== evidence.value?.inspection?.id) { acknowledged.value = false; counts.value = {} }
    evidence.value = result; error.value = ''
  } catch (err) { if (!stopped) error.value = err.message }
  finally { loading.value = false }
}
async function capture() {
  if (busy.value || loading.value) return
  busy.value = true; error.value = ''
  try { await api.post(`/operations/sessions/${props.sessionId}/inspection/capture`, {}) }
  catch (err) { error.value = err.message }
  finally { busy.value = false }
  if (!error.value) await load()
}
async function confirm() {
  if (!canConfirm.value || busy.value) return
  busy.value = true; error.value = ''
  try {
    const result = await api.post(`/operations/sessions/${props.sessionId}/confirm-return`, {
      inspectionId: inspection.value.id, physicalCheck: !inspection.value.imageDataUrl, condition: condition.value, note: note.value.trim(),
      checkedItems: evidence.value.expected.map(item => ({ snapshotId: item.snapshotId, quantity: Number(counts.value[item.snapshotId] || 0) }))
    })
    emit('confirmed', result); await load()
  } catch (err) { error.value = err.message }
  finally { busy.value = false }
}
onMounted(() => { load(); timer = setInterval(load, 5000) })
onUnmounted(() => { stopped = true; clearInterval(timer) })
</script>

<template>
  <section class="my-4 space-y-3 rounded-xl border border-blue-100 bg-white p-4">
    <h3 class="font-semibold">Xác minh trả đồ · Phiếu #{{ sessionId }}</h3>
    <p class="text-sm text-slate-600">Ảnh trong hộc được đối chiếu với danh sách của phiên trả. Phiếu chỉ hoàn tất sau khi quản trị viên xác nhận.</p>
    <p v-if="error" role="alert" class="text-sm text-red-600">{{ error }}</p>
    <p v-if="!evidence && loading" class="text-sm">Đang tải bằng chứng…</p>
    <template v-if="evidence">
      <RfidSummary :value="evidence.rfid" />
      <p v-if="inspection" class="text-sm" role="status">
        <b>{{ inspection.status === 'PASS' ? 'AI đề xuất đủ đồ — chờ xác nhận' : 'Cần kiểm tra' }}</b> · {{ inspection.reason }}
      </p>
      <p v-else class="text-sm text-amber-700">Đang chờ ảnh kiểm tra. Hệ thống sẽ thử chụp sau khi cửa đóng.</p>
      <figure v-if="inspection?.imageDataUrl" class="space-y-1">
        <div class="relative aspect-[4/3] w-full max-w-[640px] overflow-hidden rounded-lg bg-slate-100">
          <img :src="inspection.imageDataUrl" alt="Ảnh mới bên trong hộc của phiên trả" class="h-full w-full object-contain" />
          <svg v-if="boxes.length" viewBox="0 0 640 480" class="pointer-events-none absolute inset-0 h-full w-full" aria-hidden="true">
            <g v-for="(box, index) in boxes" :key="index">
              <rect :x="box.box[0]" :y="box.box[1]" :width="Math.max(0, box.box[2] - box.box[0])" :height="Math.max(0, box.box[3] - box.box[1])" fill="none" stroke="#22c55e" stroke-width="3" />
              <text :x="box.box[0] + 3" :y="Math.max(16, box.box[1] - 4)" fill="white" stroke="black" stroke-width="0.5" font-size="15">{{ box.label }} {{ Math.round(box.confidence * 100) }}%</text>
            </g>
          </svg>
        </div>
        <figcaption class="text-xs text-slate-500">Ảnh #{{ inspection.id }} · {{ new Date(inspection.capturedAtUtc + (inspection.capturedAtUtc.endsWith('Z') ? '' : 'Z')).toLocaleString('vi-VN') }}</figcaption>
      </figure>
      <button :disabled="busy || loading || !evidence.canCapture" @click="capture" class="min-h-11 rounded-xl border border-blue-200 px-4 text-sm disabled:opacity-50">{{ busy ? 'Đang xử lý…' : 'Chụp lại ảnh hộc' }}</button>
      <p class="text-xs text-slate-500">Nếu camera đang bận, đóng trang xem trực tiếp camera rồi chụp lại.</p>
      <ul class="space-y-2 text-sm">
        <li v-for="item in evidence.expected" :key="item.snapshotId" class="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 p-3">
          <span>{{ item.name }} · Cần trả: <b>{{ item.quantity }}</b><span v-if="Number.isInteger(observed(item.snapshotId))"> · AI thấy: {{ observed(item.snapshotId) }}</span></span>
          <label v-if="admin">Đã đối chiếu
            <input v-model="counts[item.snapshotId]" :disabled="busy" type="number" min="0" max="10000" step="1" :aria-label="'Số lượng trả ' + item.name" class="ml-2 min-h-11 w-20 rounded border border-slate-200 px-2" />
          </label>
        </li>
      </ul>
      <p v-if="!evidence.expected.length" class="text-sm text-amber-700">Phiếu chưa có danh sách thiết bị bàn giao; chưa thể xác nhận trả đủ.</p>
      <div v-if="admin" class="space-y-3 border-t border-slate-100 pt-3">
        <select v-model="condition" :disabled="busy" aria-label="Tình trạng trả đồ" class="min-h-11 w-full rounded-lg border border-slate-200 px-3">
          <option value="BINH_THUONG">Đã trả đủ, bình thường</option>
          <option value="HONG_HOC">Đã trả đủ, có hỏng hóc</option>
          <option value="MAT_DO">Thiếu đồ, giữ phiếu chờ xử lý</option>
        </select>
        <textarea v-model="note" :disabled="busy" maxlength="2000" aria-label="Kết quả đối chiếu" placeholder="Ghi kết quả đối chiếu ảnh, RFID hoặc kiểm tra thực tế (bắt buộc)" class="w-full rounded-lg border border-slate-200 p-3" />
        <label class="flex items-start gap-2 text-sm"><input v-model="acknowledged" :disabled="busy" type="checkbox" class="mt-1" /><span>{{ inspection?.imageDataUrl ? 'Tôi đã đối chiếu ảnh mới nhất và kiểm tra danh sách thiết bị; kết quả AI chỉ hỗ trợ việc xác nhận.' : 'Không có ảnh hộc. Tôi đã trực tiếp kiểm tra bên trong hộc và đối chiếu danh sách thiết bị.' }}</span></label>
        <button :disabled="busy || !canConfirm" @click="confirm" class="min-h-11 rounded-xl bg-brand px-4 text-white disabled:opacity-50">{{ condition === 'MAT_DO' ? 'Ghi nhận thiếu đồ' : 'Xác nhận trả đồ' }}</button>
      </div>
    </template>
  </section>
</template>
