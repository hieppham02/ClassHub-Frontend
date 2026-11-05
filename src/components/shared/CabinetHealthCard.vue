<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import AppModal from '@/components/shared/AppModal.vue'

const props = defineProps({ value: { type: Object, default: null }, online: Boolean, name: { type: String, default: '' } })
const show = ref(false), trigger = ref(null), dialog = ref(null)
const receivedOnClient = ref(performance.now()), clock = ref(performance.now())
let timer
watch(() => props.value?.receivedAtUtc, () => { receivedOnClient.value = performance.now(); clock.value = performance.now() })
const metrics = computed(() => props.value?.metrics || {})
const age = computed(() => props.value ? Math.max(0, Number(props.value.ageSeconds || 0) + (clock.value - receivedOnClient.value) / 1000) : null)
const errors = { NVS_STORAGE_FAULT: 'Lỗi lưu trữ NVS', SECURITY_NOT_PROVISIONED: 'Chưa cấp dữ liệu bảo mật',
  CLOCK_ROLLBACK: 'Đồng hồ lùi, lệnh mới đang bị chặn', TIME_NOT_SYNCED: 'Chưa đồng bộ giờ',
  RFID_NOT_READY: 'Đầu đọc RFID chưa sẵn sàng', CAMERA_NO_RECENT_FRAME: 'Chưa nhận khung camera gần đây' }
function memory(value) { return Number.isFinite(value) ? (value / 1024).toFixed(0) + ' KiB' : 'Chưa có số đo' }
function scanAge(value) { return value == null || value < 0 ? 'Chưa có lượt quét' : Math.round(value / 1000) + ' giây trước lúc đo' }
function close() {
  show.value = false
  nextTick(() => trigger.value?.focus())
}
function escape(event) { if (show.value && event.key === 'Escape') close() }
watch(show, async open => {
  clearInterval(timer)
  if (!open) return
  clock.value = performance.now()
  timer = setInterval(() => { clock.value = performance.now() }, 10000)
  await nextTick()
  dialog.value?.$el?.querySelector('button[aria-label="Đóng hộp thoại"]')?.focus()
})
onMounted(() => window.addEventListener('keydown', escape))
onUnmounted(() => { clearInterval(timer); window.removeEventListener('keydown', escape) })
</script>
<template>
  <button ref="trigger" type="button" aria-haspopup="dialog" :aria-expanded="show" @click="show = true"
    class="mt-1 inline-flex min-h-8 items-center gap-1 text-xs font-normal text-blue-700 hover:text-blue-900 hover:underline">
    Sức khỏe thiết bị
  </button>
  <Teleport to="body">
    <AppModal v-if="show" ref="dialog" :title="'Sức khỏe thiết bị' + (name ? ' · ' + name : '')" size="lg"
      class="whitespace-normal text-sm font-normal text-slate-600" @close="close">
      <div v-if="value" class="space-y-2">
        <p>Lần nhận cuối: {{ new Date(value.receivedAtUtc).toLocaleString('vi-VN') }} · {{ Math.floor(age) }} giây trước</p>
        <p>Firmware: {{ metrics.firmwareId }} · {{ metrics.firmwareVersion }}</p>
        <p>Wi-Fi: {{ metrics.rssi == null ? 'Chưa có số đo' : metrics.rssi + ' dBm' }}</p>
        <p>Bộ nhớ trống: {{ memory(metrics.heapFree) }} · Khối lớn nhất: {{ memory(metrics.heapLargest) }}</p>
        <p>PSRAM trống: {{ memory(metrics.psramFree) }}</p>
        <p>Cửa cảm biến: {{ metrics.doorOpen == null ? 'Chưa có số đo' : metrics.doorOpen ? 'Mở' : 'Đóng' }}</p>
        <p>RFID: {{ metrics.readerInitialized ? 'Đã khởi tạo' : 'Chưa sẵn sàng' }} · {{ scanAge(metrics.lastRfidScanAgeMs) }}</p>
        <p>Camera: {{ metrics.cameraRecentFrame ? 'Có khung gần lúc đo' : 'Chưa thấy khung mới' }} · {{ (Number(metrics.cameraFps100 || 0) / 100).toFixed(2) }} FPS</p>
        <p>Đồng hồ: {{ value.quality === 'CLOCK_SYNCED' ? 'Đã đồng bộ khi đo' : 'Chưa xác nhận đồng bộ' }}</p>
        <p>Wi-Fi AP: {{ metrics.apOpen === true ? 'Mạng mở, không mật khẩu' : metrics.securityProvisioned ? 'Đã cấp mật khẩu riêng' : 'Chưa rõ' }}</p>
        <p v-if="metrics.currentError" class="text-red-700">Hiện tại: {{ errors[metrics.currentError] || metrics.currentError }}</p>
        <p v-if="metrics.lastError">Lỗi gần nhất: {{ errors[metrics.lastError] || metrics.lastError }}<span v-if="metrics.lastErrorAtUtc"> · {{ new Date(metrics.lastErrorAtUtc).toLocaleString('vi-VN') }}</span></p>
      </div>
      <p v-else class="py-4 text-slate-500">Chưa ghi nhận thông tin sức khỏe của tủ này.</p>
    </AppModal>
  </Teleport>
</template>
