<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { api } from '@/services/apiClient.js'
const props = defineProps({ room: { type: String, default: '' } })
const alerts = ref([]), history = ref([]), error = ref(''), loading = ref(false), nextBefore = ref(null)
const showResolved = ref(false)
const registerOpen = ref(false), nodeCode = ref(''), nodeName = ref(''), nodeInterval = ref(30), registered = ref('')
async function registerNode() {
  error.value = ''; registered.value = ''
  try { await api.post('/admin/assets/nodes', { nodeCode: nodeCode.value.trim(), name: nodeName.value.trim(), roomId: props.room, publishIntervalSeconds: Number(nodeInterval.value) }); registered.value = 'Đã đăng ký. Node giữ trạng thái ngoại tuyến đến khi nhận bản tin hợp lệ.'; registerOpen.value = false }
  catch (err) { error.value = err.message }
}
const labels = { DOOR_OPEN_LONG: 'Cửa mở quá lâu', CABINET_MESSAGES_MISSING: 'Tủ ngừng gửi bản tin', NODE_MESSAGES_MISSING: 'Node cảm biến ngừng gửi bản tin', AFTER_RETURN_CURRENT: 'Dòng điện còn cao sau trả' }
let version = 0, timer
function utc(value) {
  if (!value) return 'Chưa rõ'
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : value + 'Z').toLocaleString('vi-VN')
}
async function load(append = false) {
  const request = ++version
  loading.value = true; error.value = ''
  const query = new URLSearchParams()
  if (props.room) query.set('room', props.room)
  if (!showResolved.value) query.set('status', 'OPEN')
  try {
    const [data, samples] = await Promise.all([
      api.get(`/admin/operations-telemetry/alerts?${query}`),
      props.room ? api.get(`/admin/operations-telemetry/cabinets/${encodeURIComponent(props.room)}/history?hours=24${append && nextBefore.value ? '&before=' + nextBefore.value : ''}`) : Promise.resolve(null)
    ])
    if (request !== version) return
    alerts.value = data.items
    history.value = append ? [...history.value, ...(samples?.items || [])] : samples?.items || []
    nextBefore.value = samples?.nextBefore || null
  } catch (err) { if (request === version) error.value = err.message }
  finally { if (request === version) loading.value = false }
}
watch([() => props.room, showResolved], () => { history.value = []; nextBefore.value = null; load() })
onMounted(() => { load(); timer = setInterval(() => { if (!loading.value) load() }, 15000) })
onUnmounted(() => { version++; clearInterval(timer) })
</script>
<template>
  <section class="my-4 rounded-2xl border border-blue-100 bg-white p-5">
    <div class="flex flex-wrap items-center gap-3">
      <h3 class="mr-auto font-bold">Cảnh báo vận hành · Dữ liệu thật</h3>
      <label class="text-sm"><input v-model="showResolved" type="checkbox"> Xem cả đã kết thúc</label>
      <button class="rounded border px-3 py-1 text-sm" :disabled="loading" @click="load()">Cập nhật</button>
    </div>
    <p class="my-2 text-xs text-slate-500">Quy tắc vận hành dựa trên bản tin đo được. Cảm biến dòng điện phản ánh tổng phòng; không xác định từng thiết bị. Chưa có bản tin thật không có nghĩa tủ đang tốt.</p>
    <p v-if="error" role="alert" class="text-sm text-red-700">{{ error }}</p>
    <p v-else-if="!alerts.length" class="py-3 text-sm text-slate-500">{{ loading ? 'Đang tải…' : 'Chưa có cảnh báo trong phạm vi này.' }}</p>
    <ul v-else class="divide-y">
      <li v-for="a in alerts" :key="a.id" class="py-2 text-sm">
        <strong>{{ a.roomId }} · {{ labels[a.rule] || a.rule }}</strong>
        <span :class="a.status === 'OPEN' ? 'text-amber-700' : 'text-green-700'"> · {{ a.status === 'OPEN' ? 'Cần kiểm tra' : 'Đã hết điều kiện cảnh báo' }}</span>
        <p class="text-xs text-slate-500">Phát hiện {{ utc(a.startedAtUtc) }} · Kiểm tra {{ utc(a.lastEvaluatedAtUtc) }}</p>
        <p v-if="a.evidence?.assessment" class="text-xs">{{ a.evidence.assessment.CurrentAmperes }} A · Ngưỡng {{ a.evidence.assessment.ThresholdAmperes }} A</p>
      </li>
    </ul>
    <div v-if="room" class="mt-3">
      <button class="text-sm text-blue-700" @click="registerOpen = !registerOpen">Đăng ký node cảm biến cho {{ room }}</button>
      <p v-if="registered" role="status" class="text-sm text-green-700">{{ registered }}</p>
      <form v-if="registerOpen" class="my-3 flex flex-wrap gap-3" @submit.prevent="registerNode">
        <label class="text-xs">Mã node<input v-model="nodeCode" required pattern="[A-Za-z0-9_-]{1,50}" maxlength="50" class="block rounded border p-2"></label>
        <label class="text-xs">Tên node<input v-model="nodeName" required maxlength="100" class="block rounded border p-2"></label>
        <label class="text-xs">Chu kỳ gửi (giây)<input v-model="nodeInterval" required type="number" min="1" max="1200" class="block w-28 rounded border p-2"></label>
        <button class="self-end rounded border p-2 text-sm">Lưu đăng ký</button>
        <p class="w-full text-xs text-slate-500">Mã phải khớp thiết bị. Cấu hình tài khoản MQTT riêng và quyền gửi đúng topic cho node trước khi kết nối; đăng ký này chỉ lưu danh mục.</p>
      </form>
    </div>
    <details v-if="room" class="mt-4">
      <summary class="cursor-pointer text-sm font-semibold">Lịch sử tủ {{ room }} trong 24 giờ</summary>
      <p v-if="!history.length" class="py-3 text-sm text-slate-500">Chưa có dữ liệu thật cho tủ này.</p>
      <div v-else class="max-h-72 overflow-auto">
        <table class="w-full text-left text-xs"><thead><tr><th>Server nhận</th><th>Cửa</th><th>Wi-Fi</th><th>Thời gian thiết bị</th></tr></thead>
          <tbody><tr v-for="s in history" :key="s.id" class="border-t"><td class="py-2">{{ utc(s.receivedAtUtc) }}</td><td>{{ s.doorOpen === true ? 'Mở' : s.doorOpen === false ? 'Đóng' : 'Chưa rõ' }}</td><td>{{ s.metrics?.rssi ?? '—' }} dBm</td><td>{{ s.metrics?.clockSynced ? utc(s.metrics.measuredAtUtc) : 'Chưa đồng bộ' }}</td></tr></tbody>
        </table>
      </div>
      <button v-if="nextBefore" class="mt-2 text-sm text-blue-700" :disabled="loading" @click="load(true)">Tải các mẫu trước</button>
    </details>
  </section>
</template>
