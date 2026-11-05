<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
const props = defineProps({ value: { type: Object, default: null }, online: Boolean })
const receivedOnClient = ref(performance.now()), clock = ref(performance.now())
let timer
watch(() => props.value?.receivedAtUtc, () => { receivedOnClient.value = performance.now(); clock.value = performance.now() })
const metrics = computed(() => props.value?.metrics || {})
const age = computed(() => props.value ? Math.max(0, Number(props.value.ageSeconds || 0) + (clock.value - receivedOnClient.value) / 1000) : null)
const stale = computed(() => age.value === null || age.value > 45 || !props.online)
const errors = { NVS_STORAGE_FAULT: 'Lỗi lưu trữ NVS', SECURITY_NOT_PROVISIONED: 'Chưa cấp dữ liệu bảo mật',
  CLOCK_ROLLBACK: 'Đồng hồ lùi, lệnh mới đang bị chặn', TIME_NOT_SYNCED: 'Chưa đồng bộ giờ',
  RFID_NOT_READY: 'Đầu đọc RFID chưa sẵn sàng', CAMERA_NO_RECENT_FRAME: 'Chưa nhận khung camera gần đây' }
function memory(value) { return Number.isFinite(value) ? (value / 1024).toFixed(0) + ' KiB' : 'Chưa có số đo' }
function scanAge(value) { return value == null || value < 0 ? 'Chưa có lượt quét' : Math.round(value / 1000) + ' giây trước lúc đo' }
onMounted(() => { timer = setInterval(() => { clock.value = performance.now() }, 10000) })
onUnmounted(() => clearInterval(timer))
</script>
<template>
  <details class="mt-2 max-w-sm whitespace-normal text-xs font-normal text-slate-600">
    <summary class="min-h-8 cursor-pointer" :class="stale ? 'text-amber-700' : 'text-emerald-700'">Sức khỏe thiết bị · {{ value ? stale ? 'Dữ liệu cũ/mất liên lạc' : 'Có số đo mới' : 'Chưa có telemetry' }}</summary>
    <div v-if="value" class="space-y-1 rounded-lg bg-slate-50 p-3">
      <p>Lần nhận cuối: {{ new Date(value.receivedAtUtc).toLocaleString('vi-VN') }} · {{ Math.floor(age) }} giây</p>
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
      <p class="text-slate-400">Số đo REAL; khởi tạo đầu đọc chưa chứng minh RF tốt, nhận khung camera chưa chứng minh ảnh đủ rõ.</p>
    </div>
    <p v-else class="mt-2">Firmware cũ chưa gửi số đo hoặc chưa nhận dữ liệu. Không suy ra thiết bị đang tốt.</p>
  </details>
</template>
