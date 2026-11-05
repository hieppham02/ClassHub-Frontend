<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api } from '@/services/apiClient.js'
const props = defineProps({ sessionId: { type: Number, required: true } })
const progress = ref(null), error = ref(''), notice = ref(''), busy = ref(false)
let timer, stopped = false, loading = false
const stages = computed(() => {
  const p = progress.value || {}
  return [
    { name: 'Yêu cầu đã ghi nhận', done: p.requestRecorded },
    { name: 'Tủ xác nhận lệnh', done: p.deviceAcknowledged },
    { name: 'Đã kích relay', done: p.relayTriggered },
    { name: 'Cảm biến thấy cửa mở', done: p.doorOpened },
    { name: 'Cửa đã đóng', done: p.doorClosed },
    ...(p.purpose === 'RETURN' ? [{ name: 'Kiểm tra thiết bị', done: p.completed, pending: p.needsReview }] : []),
    { name: p.purpose === 'RETURN' ? 'Hoàn tất trả' : 'Hoàn tất nhận', done: p.completed }
  ]
})
const help = computed(() => {
  const p = progress.value
  if (!p) return ''
  if (p.completed) return p.purpose === 'RETURN' ? 'Lượt trả đã được xác nhận.' : 'Lượt nhận hoàn tất, phiên mượn đang diễn ra.'
  if (!p.isOnline) return 'Tủ đang ngoại tuyến. Kiểm tra nguồn/mạng; hệ thống sẽ đồng bộ khi tủ kết nối lại.'
  if (p.phase === 'RETURN_FAILED') return 'Có bằng chứng hoặc thiết bị cần kiểm tra. Xem RFID/ảnh và liên hệ quản trị viên.'
  if (p.failed) return 'Tủ báo lệnh chưa thực hiện được. Kiểm tra trạng thái trước khi cấp lại QR.'
  if (p.needsReview) return 'Đã đóng cửa. Chờ đối chiếu RFID/ảnh và quản trị viên xác nhận; không cần tạo thêm lệnh mở.'
  if (p.doorOpened && !p.doorClosed) return 'Quét từng thẻ, hoàn tất lấy/đặt đồ rồi đóng cửa tủ.'
  if (p.relayTriggered && !p.doorOpened) return 'Tủ đã kích relay nhưng chưa thấy cửa mở. Kiểm tra chốt/cửa; gửi lại cùng lệnh không tạo xung mở mới.'
  if (p.requestRecorded && !p.deviceAcknowledged) return 'Chưa có phản hồi tủ. Kiểm tra kết nối; có thể gửi lại đúng lệnh đang chờ.'
  return 'Quét QR tại tủ để bắt đầu lượt thao tác.'
})
async function refresh() {
  if (loading) return
  loading = true
  try { const result = await api.get(`/operations/sessions/${props.sessionId}/progress`); if (!stopped) { progress.value = result; error.value = '' } }
  catch (err) { if (!stopped) error.value = err.message }
  finally { loading = false }
}
async function retry() {
  if (busy.value) return
  busy.value = true; error.value = ''; notice.value = ''
  try { const result = await api.post(`/cabinet/qr/${props.sessionId}/retry`, {}); notice.value = result.message; await refresh() }
  catch (err) { error.value = err.message }
  finally { busy.value = false }
}
onMounted(() => { refresh(); timer = setInterval(refresh, 3000) })
onUnmounted(() => { stopped = true; clearInterval(timer) })
</script>
<template>
  <section class="space-y-3 rounded-xl border border-blue-100 p-4">
    <h3 class="text-sm font-bold">Tiến trình {{ progress?.purpose === 'RETURN' ? 'trả' : 'nhận' }} thiết bị</h3>
    <ol class="grid gap-2 text-sm sm:grid-cols-2" aria-live="polite">
      <li v-for="(stage, index) in stages" :key="stage.name" class="rounded-lg px-3 py-2" :class="stage.done ? 'bg-emerald-50 text-emerald-800' : stage.pending ? 'bg-amber-50 text-amber-800' : 'bg-slate-50 text-slate-500'">
        {{ stage.done ? '✓' : index + 1 }} · {{ stage.name }}<span v-if="stage.pending"> · Đang chờ</span>
      </li>
    </ol>
    <p v-if="help" class="text-sm text-slate-600">{{ help }}</p>
    <p v-if="progress?.legacy" class="text-xs text-amber-700">Firmware cũ chưa tách đủ mốc cảm biến. Một số bước chỉ được xác định khi tủ báo đã đóng.</p>
    <p v-if="error" role="alert" class="text-sm text-red-600">{{ error }}</p>
    <p v-if="notice" role="status" class="text-sm text-emerald-700">{{ notice }}</p>
    <button v-if="progress?.canRetrySameCommand" :disabled="busy" @click="retry" class="min-h-11 rounded-xl border border-blue-200 px-3 text-sm disabled:opacity-50">Gửi lại cùng lệnh đang chờ</button>
  </section>
</template>
