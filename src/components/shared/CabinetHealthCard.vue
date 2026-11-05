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
const door = computed(() => metrics.value.doorOpen === true ? 'Mở' : metrics.value.doorOpen === false ? 'Đóng' : 'Chưa có số đo')
const reader = computed(() => metrics.value.readerInitialized === true ? 'Đã khởi tạo' : metrics.value.readerInitialized === false ? 'Chưa khởi tạo' : 'Chưa có số đo')
const camera = computed(() => metrics.value.cameraRecentFrame === true ? 'Có khung hình' : metrics.value.cameraRecentFrame === false ? 'Chưa có khung mới' : 'Chưa có số đo')
const fps = computed(() => Number.isFinite(metrics.value.cameraFps100) ? (metrics.value.cameraFps100 / 100).toFixed(2) : '—')
const accessPoint = computed(() => metrics.value.apOpen === true ? 'Mạng mở' : metrics.value.securityProvisioned === true ? 'Có mật khẩu riêng' : 'Chưa có thông tin')
const memoryCards = computed(() => [
  { label: 'Heap trống', value: metrics.value.heapFree },
  { label: 'Khối trống lớn nhất', value: metrics.value.heapLargest },
  { label: 'PSRAM trống', value: metrics.value.psramFree }
].map(item => {
  const valid = Number.isFinite(item.value) && item.value >= 0
  const mib = valid && item.value >= 1048576
  return { label: item.label, amount: valid ? (item.value / (mib ? 1048576 : 1024)).toFixed(mib ? 2 : 0) : '—', unit: valid ? mib ? 'MiB' : 'KiB' : '' }
}))
function scanAge(value) { return value == null || value < 0 ? 'Chưa có lượt quét' : Math.round(value / 1000) + ' giây trước lần đo' }
function formatDate(value) { return value ? new Date(value).toLocaleString('vi-VN') : 'Chưa ghi nhận' }
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
  <button ref="trigger" type="button" aria-haspopup="dialog" :aria-expanded="show"
    :aria-label="'Xem thông tin tủ ' + name" @click="show = true"
    class="inline-flex min-h-9 items-center rounded-md text-left font-bold text-slate-900 underline-offset-4 transition hover:text-blue-700 hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-500">
    {{ name || 'Thông tin tủ' }}
  </button>
  <Teleport to="body">
    <AppModal v-if="show" ref="dialog" :title="'Thông tin tủ' + (name ? ' · ' + name : '')" size="xl"
      class="whitespace-normal text-sm font-normal text-slate-600" @close="close">
      <div class="mb-5 flex flex-wrap items-center justify-between gap-3">
        <span class="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold"
          :class="online ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'">
          <span class="size-2 rounded-full" :class="online ? 'bg-emerald-500' : 'bg-slate-400'"></span>
          {{ online ? 'Online' : 'Offline' }}
        </span>
        <div v-if="value" class="text-right text-xs">
          <p class="font-medium text-slate-700">Nhận {{ Math.floor(age) }} giây trước</p>
          <p class="mt-0.5 text-slate-400">{{ formatDate(value.receivedAtUtc) }}</p>
        </div>
      </div>

      <div v-if="value" class="space-y-5">
        <section v-if="metrics.currentError" class="rounded-xl border border-red-200 bg-red-50 p-4" role="status">
          <h3 class="flex items-center gap-2 font-semibold text-red-800">
            <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M10.3 3.8 2.6 17.2A2 2 0 0 0 4.3 20h15.4a2 2 0 0 0 1.7-2.8L13.7 3.8a2 2 0 0 0-3.4 0Z"/></svg>
            Cần kiểm tra
          </h3>
          <p class="mt-1 break-words text-sm text-red-700">{{ errors[metrics.currentError] || metrics.currentError }}</p>
        </section>

        <section aria-label="Cảm biến" class="space-y-3">
          <h3 class="section-title">Cảm biến</h3>
          <div class="grid gap-3 sm:grid-cols-3">
            <div class="sensor-card">
              <div class="sensor-label"><svg class="sensor-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M4 21h16M7 21V3h10v18M13 12h.01"/></svg>Cửa tủ</div>
              <p class="mt-3 text-lg font-bold" :class="metrics.doorOpen === true ? 'text-amber-700' : metrics.doorOpen === false ? 'text-emerald-700' : 'text-slate-500'">{{ door }}</p>
              <p class="sensor-note">Trạng thái cảm biến</p>
            </div>
            <div class="sensor-card">
              <div class="sensor-label"><svg class="sensor-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path stroke-linecap="round" d="M7 9h3v6H7zm7 1c1 1 1 3 0 4m3-6c2 2 2 6 0 8"/></svg>RFID</div>
              <p class="mt-3 font-bold" :class="metrics.readerInitialized === true ? 'text-emerald-700' : 'text-slate-600'">{{ reader }}</p>
              <p class="sensor-note">{{ scanAge(metrics.lastRfidScanAgeMs) }}</p>
            </div>
            <div class="sensor-card">
              <div class="sensor-label"><svg class="sensor-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path stroke-linejoin="round" d="m8 6 1-2h6l1 2h3a2 2 0 0 1 2 2v11H3V8a2 2 0 0 1 2-2h3Z"/><circle cx="12" cy="12" r="3"/></svg>Camera</div>
              <p class="mt-3 font-bold text-slate-900">{{ fps }} <span class="text-xs font-medium text-slate-400">FPS</span></p>
              <p class="sensor-note" :class="metrics.cameraRecentFrame === false ? 'text-amber-700' : ''">{{ camera }}</p>
            </div>
          </div>
        </section>

        <section aria-label="Kết nối" class="rounded-xl border border-slate-200 p-4">
          <h3 class="section-title">Kết nối</h3>
          <div class="mt-3 grid gap-4 sm:grid-cols-[1fr_1.5fr]">
            <div class="flex items-center gap-3">
              <span class="flex size-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path stroke-linecap="round" d="M2 8a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0m-11 4a6 6 0 0 1 8 0"/><circle cx="12" cy="20" r=".8"/></svg>
              </span>
              <div><p class="text-xs text-slate-500">Tín hiệu Wi-Fi</p><p class="mt-1 text-lg font-bold text-slate-900">{{ metrics.rssi ?? '—' }} <span v-if="metrics.rssi != null" class="text-xs font-medium text-slate-400">dBm</span></p></div>
            </div>
            <dl class="space-y-2 text-xs">
              <div class="flex justify-between gap-4"><dt class="text-slate-500">Đồng hồ</dt><dd class="text-right font-medium" :class="value.quality === 'CLOCK_SYNCED' ? 'text-emerald-700' : 'text-slate-600'">{{ value.quality === 'CLOCK_SYNCED' ? 'Đã đồng bộ' : 'Chưa xác nhận' }}</dd></div>
              <div class="flex justify-between gap-4"><dt class="text-slate-500">Cấu hình Wi-Fi AP</dt><dd class="text-right font-medium text-slate-700">{{ accessPoint }}</dd></div>
            </dl>
          </div>
        </section>

        <section aria-label="Bộ nhớ" class="space-y-3">
          <h3 class="section-title">Bộ nhớ</h3>
          <div class="grid grid-cols-3 gap-2 sm:gap-3">
            <div v-for="item in memoryCards" :key="item.label" class="rounded-xl bg-slate-50 p-3 sm:p-4">
              <p class="min-h-8 text-[11px] leading-4 text-slate-500">{{ item.label }}</p>
              <p class="mt-1 text-lg font-bold tabular-nums text-slate-900 sm:text-xl">{{ item.amount }}</p>
              <p class="mt-0.5 text-xs text-slate-400">{{ item.unit || 'Chưa có số đo' }}</p>
            </div>
          </div>
        </section>

        <section aria-label="Hệ thống" class="rounded-xl border border-slate-200 p-4">
          <h3 class="section-title">Hệ thống</h3>
          <dl class="mt-3 space-y-2 text-xs">
            <div class="flex justify-between gap-4"><dt class="shrink-0 text-slate-500">Phiên bản</dt><dd class="font-semibold text-slate-700">{{ metrics.firmwareVersion || '—' }}</dd></div>
            <div class="flex justify-between gap-4"><dt class="shrink-0 text-slate-500">Mã firmware</dt><dd class="min-w-0 break-all text-right font-mono text-slate-600">{{ metrics.firmwareId || 'Chưa ghi nhận' }}</dd></div>
          </dl>
        </section>

        <section v-if="metrics.lastError && metrics.lastError !== metrics.currentError" class="rounded-xl border border-amber-100 bg-amber-50/60 p-4">
          <h3 class="text-xs font-semibold text-amber-900">Lỗi gần nhất đã ghi nhận</h3>
          <p class="mt-1 break-words text-sm text-amber-800">{{ errors[metrics.lastError] || metrics.lastError }}</p>
          <p v-if="metrics.lastErrorAtUtc" class="mt-1 text-xs text-amber-700">{{ formatDate(metrics.lastErrorAtUtc) }}</p>
        </section>
      </div>
      <div v-else class="rounded-xl bg-slate-50 px-4 py-8 text-center">
        <p class="font-semibold text-slate-700">Chưa có thông tin thiết bị</p>
        <p class="mt-2 text-xs text-slate-500">Thông số sẽ xuất hiện khi tủ gửi dữ liệu về hệ thống.</p>
      </div>
    </AppModal>
  </Teleport>
</template>
<style scoped>
@reference "../../style.css";
.section-title { @apply text-xs font-bold uppercase tracking-wider text-slate-500; }
.sensor-card { @apply rounded-xl border border-slate-200 p-4; }
.sensor-label { @apply flex items-center gap-2 text-xs font-semibold text-slate-600; }
.sensor-icon { @apply size-4 shrink-0 text-slate-400; }
.sensor-note { @apply mt-2 text-[11px] leading-4 text-slate-500; }
</style>
