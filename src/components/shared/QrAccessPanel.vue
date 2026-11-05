<script setup>
import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
import AppModal from '@/components/shared/AppModal.vue'
import ReturnInspectionPanel from '@/components/shared/ReturnInspectionPanel.vue'
import RfidLivePanel from '@/components/shared/RfidLivePanel.vue'
import SessionProgressPanel from '@/components/shared/SessionProgressPanel.vue'
import { api } from '@/services/apiClient.js'

const props = defineProps({ session: { type: Object, required: true } })
const emit = defineEmits(['refresh', 'request-return'])
const busy = ref(false)
const error = ref('')
const notice = ref('')
const scanning = ref(false)
const showScanner = ref(false)
const video = ref(null)
const preview = ref(null)
const token = ref('')
const purpose = computed(() => props.session.status === 'RETURNING' ? 'RETURN' : 'RECEIVE')
const phaseLabels = {
  RECEIVE_QR: 'QR nhận đồ đã gửi tới màn hình tủ.',
  RECEIVE_QR_FAILED: 'Chưa gửi được QR nhận đồ. Hãy cấp lại mã.',
  RECEIVE_OPEN_REQUESTED: 'Đang chờ tủ xác nhận mở cửa.',
  RECEIVE_UNLOCKED: 'Tủ đã kích relay, đang chờ cảm biến xác nhận cửa mở.',
  RECEIVE_OPEN: 'Sau khi cửa mở, quét lần lượt thẻ RFID của từng món, lấy đồ rồi đóng cửa.',
  IN_USE: 'Đã nhận đồ và đóng cửa. Lượt mượn đang diễn ra.',
  RETURN_QR: 'QR trả đồ đã gửi tới màn hình tủ.',
  RETURN_QR_FAILED: 'Chưa gửi được QR trả đồ. Hãy cấp lại mã.',
  RETURN_OPEN_REQUESTED: 'Đang chờ tủ mở cửa để trả đồ.',
  RETURN_UNLOCKED: 'Tủ đã kích relay, đang chờ cảm biến xác nhận cửa mở.',
  RETURN_OPEN: 'Quét lần lượt thẻ RFID của từng món, đặt đồ vào hộc rồi đóng cửa.',
  RETURN_CHECK: 'Cửa đã đóng. Đang chụp ảnh hộc và chờ quản trị viên xác minh trả đồ.',
  RETURN_FAILED: 'Có thiết bị hoặc bằng chứng cần kiểm tra. Xem kết quả xác minh và liên hệ quản trị viên.'
}
const waitingCommand = computed(() => (props.session.qrPhase || '').endsWith('_OPEN_REQUESTED'))
const mayScan = computed(() => ['PENDING', 'RETURNING'].includes(props.session.status) && !props.session.isCabinetOpen && !waitingCommand.value && !['RETURN_CHECK', 'RECEIVE_UNLOCKED', 'RETURN_UNLOCKED'].includes(props.session.qrPhase))
let controls = null
let generation = 0
let decoding = false
function stopCamera() {
  generation++
  controls?.stop(); controls = null
  video.value?.srcObject?.getTracks().forEach(track => track.stop())
  scanning.value = false
}
function closeScanner() {
  stopCamera()
  showScanner.value = false
}
async function issue() {
  if (busy.value) return
  busy.value = true; error.value = ''; preview.value = null; stopCamera()
  try {
    const data = await api.post(`/cabinet/qr/${props.session.id}/issue`, { purpose: purpose.value })
    notice.value = data.message
  } catch (err) { error.value = err.message }
  finally { busy.value = false; emit('refresh') }
}
async function scan() {
  if (busy.value || scanning.value) return
  showScanner.value = true
  error.value = ''; preview.value = null
  if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
    error.value = 'Camera cần HTTPS và quyền truy cập camera. Mở ClassHub bằng địa chỉ HTTPS.'
    return
  }
  scanning.value = true; const current = ++generation
  await nextTick()
  try {
    const { BrowserQRCodeReader } = await import('@zxing/browser')
    if (current !== generation) return
    const reader = new BrowserQRCodeReader()
    const started = await reader.decodeFromConstraints({
      video: { facingMode: { ideal: 'environment' }, width: { ideal: 1920 }, height: { ideal: 1080 } },
      audio: false
    }, video.value, async (result, _, scanner) => {
      if (!result || decoding || current !== generation) return
      decoding = true
      scanner.stop()
      const raw = result.getText()
      stopCamera()
      try {
        const match = /^classhub:qr:v1:([A-Fa-f0-9]{64})$/.exec(raw)
        if (!match) throw new Error('Mã này không phải QR nhận/trả của ClassHub.')
        token.value = match[1]
        busy.value = true
        preview.value = await api.post(`/cabinet/qr/${props.session.id}/preview`, { token: token.value, purpose: purpose.value })
        showScanner.value = false
      } catch (err) { error.value = err.message }
      finally { busy.value = false; decoding = false }
    })
    if (current !== generation) started.stop()
    else {
      controls = started
      const track = video.value?.srcObject?.getVideoTracks()[0]
      const capabilities = track?.getCapabilities?.() || {}
      const preferences = []
      if (capabilities.focusMode?.includes('continuous')) preferences.push({ focusMode: 'continuous' })
      if (capabilities.exposureMode?.includes('continuous')) preferences.push({ exposureMode: 'continuous' })
      if (capabilities.torch) preferences.push({ torch: false })
      for (const preference of preferences) {
        if (current !== generation) break
        try {
          await track.applyConstraints({ advanced: [preference] })
        } catch {
          // Optional camera settings must not interrupt QR scanning.
        }
      }
    }
  } catch (err) {
    if (current !== generation) return
    stopCamera()
    error.value = err.name === 'NotAllowedError' ? 'Bạn chưa cấp quyền camera. Hãy cho phép camera trong trình duyệt.' : 'Không mở được camera. Kiểm tra camera và thử lại.'
  }
}
async function open() {
  if (busy.value || !preview.value) return
  busy.value = true; error.value = ''
  try {
    const data = await api.post(`/cabinet/qr/${props.session.id}/open`, { token: token.value, purpose: preview.value.purpose })
    notice.value = data.message
  } catch (err) { error.value = err.message }
  finally { preview.value = null; token.value = ''; busy.value = false; emit('refresh') }
}
async function retry() {
  if (busy.value) return
  busy.value = true; error.value = ''
  try { notice.value = (await api.post(`/cabinet/qr/${props.session.id}/retry`)).message }
  catch (err) { error.value = err.message }
  finally { busy.value = false; emit('refresh') }
}
watch(() => props.session.id, () => { closeScanner(); preview.value = null; token.value = ''; error.value = ''; notice.value = '' })
watch(mayScan, (allowed) => { if (!allowed) { closeScanner(); preview.value = null; token.value = '' } })
onUnmounted(stopCamera)
</script>

<template>
  <SessionProgressPanel :key="session.id" :session-id="session.id" />
  <ReturnInspectionPanel v-if="session.status === 'RETURNING' && ['RETURN_CHECK', 'RETURN_FAILED'].includes(session.qrPhase)" :session-id="session.id" />
  <section class="space-y-4">
    <h3 class="text-sm font-bold text-ink">{{ session.status === 'RETURNING' ? 'Trả đồ bằng QR' : 'Nhận đồ bằng QR' }}</h3>
    <p class="rounded-xl bg-blue-50 p-3 text-sm text-slate-700" aria-live="polite">{{ phaseLabels[session.qrPhase] || 'Quét QR trên màn hình tủ để xác nhận mở cửa.' }}</p>
    <RfidLivePanel v-if="['RECEIVE_OPEN', 'RETURN_OPEN'].includes(session.qrPhase)" :session-id="session.id" />
    <p v-if="notice" class="text-sm text-emerald-700" role="status">{{ notice }}</p>
    <p v-if="error && !showScanner" class="text-sm text-red-600" role="alert">{{ error }}</p>
    <div v-if="mayScan" class="flex flex-wrap gap-2">
      <button :disabled="busy || showScanner" @click="scan" class="modal-primary">Quét mã QR</button>
      <button :disabled="busy" @click="issue" class="modal-cancel">Cấp lại QR</button>
    </div>
    <p v-if="mayScan" class="text-xs text-slate-500">QR có hiệu lực 3 phút. Nếu mã trên màn hình tủ hết hạn, hãy cấp lại QR.</p>
    <Teleport to="body">
      <AppModal v-if="showScanner" title="Quét mã QR tại tủ" size="lg" layer="nested" :busy="busy" @close="closeScanner">
        <div class="space-y-3">
          <video v-if="scanning" ref="video" autoplay muted playsinline class="max-h-[50dvh] min-h-48 w-full rounded-xl bg-slate-900 object-contain" />
          <p class="text-sm text-slate-500">Giữ điện thoại ổn định, đưa toàn bộ mã QR và viền trắng vào khung. Lùi nhẹ nếu camera chưa lấy nét và tránh ánh sáng phản chiếu trên màn hình tủ.</p>
          <p v-if="busy" class="text-sm text-slate-500" role="status">Đang kiểm tra mã QR...</p>
          <p v-if="error" class="text-sm text-red-600" role="alert">{{ error }}</p>
        </div>
        <template #footer>
          <button :disabled="busy" @click="closeScanner" class="modal-cancel">Đóng</button>
          <button v-if="!scanning" :disabled="busy" @click="scan" class="modal-primary">Quét lại</button>
        </template>
      </AppModal>
    </Teleport>
    <button v-if="['IN_USE', 'ACTIVE'].includes(session.status) && !session.isCabinetOpen" @click="emit('request-return')" class="modal-primary w-full">Trả đồ · Tạo QR tại tủ</button>
    <AppModal v-if="preview" title="Xác nhận mở cửa tủ" layer="nested" :busy="busy" @close="preview = null; token = ''">
      <p class="text-sm">{{ preview.roomName }} · Phiếu #{{ preview.sessionId }}</p>
      <p class="mt-3 text-sm text-slate-500">{{ preview.purpose === 'RETURN' ? 'Mở cửa để trả đồ. Đóng cửa để chụp ảnh và chờ xác minh.' : 'Mở cửa để nhận đồ. Đóng cửa sau khi lấy đồ.' }}</p>
      <template #footer><button :disabled="busy" @click="preview = null; token = ''" class="modal-cancel">Hủy</button><button :disabled="busy" @click="open" class="modal-primary">{{ busy ? 'Đang gửi...' : 'Xác nhận mở cửa' }}</button></template>
    </AppModal>
  </section>
</template>
