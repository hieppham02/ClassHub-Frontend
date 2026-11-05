<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api } from '@/services/apiClient.js'
const props = defineProps({ cabinetId: { type: Number, required: true } })
const stock = ref([]), bindings = ref([]), latest = ref(null), selected = ref(null), equipmentId = ref('')
const busy = ref(false), loading = ref(true), error = ref(''), notice = ref(''), now = ref(Date.now())
let alive = true, timer, clock, abort = new AbortController()
const base = '/admin/cabinets/' + props.cabinetId + '/rfid/'
const messages = {
  OFFLINE: 'Tủ đang offline. Kết nối tủ để quét thẻ.',
  FIRMWARE_UPDATE_REQUIRED: 'Cập nhật firmware v13 để nhận thẻ vừa quét.',
  SYNC_REQUIRED: 'Đang chờ tủ đồng bộ thời gian. Hãy quét lại sau.',
  WAITING_FOR_SCAN: 'Đưa thẻ vào đầu đọc của tủ.',
  ALREADY_BOUND: 'Thẻ này đã được gắn với thiết bị.',
}
const expired = computed(() => selected.value && new Date(selected.value.expiresAtUtc).getTime() <= now.value)
const chosen = computed(() => stock.value.find(e => e.id === Number(equipmentId.value)))
const canSave = computed(() => selected.value && !expired.value && chosen.value && !busy.value && bindings.value.length < 32)
async function options() {
  loading.value = true
  try {
    const data = await api.get(base + 'options', { signal: abort.signal })
    if (!alive) return
    stock.value = data.stock; bindings.value = data.bindings
  } catch (e) { if (alive) error.value = e.message }
  finally { if (alive) loading.value = false }
}
async function poll() {
  try {
    const data = await api.get(base + 'latest', { signal: abort.signal })
    if (alive) latest.value = data
  } catch { if (alive) latest.value = { state: 'OFFLINE' } }
  finally { if (alive) timer = setTimeout(poll, 2500) }
}
function selectScan() {
  if (latest.value?.state !== 'READY' || busy.value) return
  selected.value = { ...latest.value.scan }; equipmentId.value = ''; error.value = ''; notice.value = ''
}
async function save() {
  if (!canSave.value) return
  busy.value = true; error.value = ''; notice.value = ''
  const data = { selectionToken: selected.value.selectionToken, stockEquipmentId: chosen.value.id, stockVersion: chosen.value.version }
  try {
    const result = await api.post(base + 'bind', data, { signal: abort.signal })
    if (alive) notice.value = result.message
  } catch (e) { if (alive) error.value = e.message + ' Kiểm tra danh sách thẻ bên dưới trước khi thao tác tiếp.' }
  finally {
    // Never automatically retry a stock-changing request after an ambiguous network result.
    if (alive) {
      selected.value = null; equipmentId.value = ''
      await options()
      busy.value = false
    }
  }
}
onMounted(() => { options(); poll(); clock = setInterval(() => { now.value = Date.now() }, 1000) })
onUnmounted(() => { alive = false; clearTimeout(timer); clearInterval(clock); abort.abort() })
</script>
<template>
  <section aria-label="Gắn thẻ RFID" class="mt-5 rounded-xl border border-slate-200 p-4">
    <div class="flex items-center justify-between gap-3">
      <h3 class="font-semibold text-slate-900">Thiết bị & thẻ RFID</h3>
      <span class="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-500">{{ bindings.length }}/32 thẻ</span>
    </div>
    <p class="mt-2 text-xs leading-5 text-slate-500">Quét thẻ → chọn thẻ → chọn thiết bị trong kho. Xác nhận sẽ chuyển 1 thiết bị vào tủ và gắn thẻ.</p>
    <div class="mt-4 space-y-4">
      <div class="rounded-lg bg-blue-50 p-3">
        <p class="text-xs font-semibold text-slate-600">1. Thẻ vừa quét</p>
        <div v-if="latest?.state === 'READY'" class="mt-2 flex flex-wrap items-center justify-between gap-2">
          <code class="font-bold text-blue-900">{{ latest.scan.uid }}</code>
          <button type="button" :disabled="busy" class="rounded-lg bg-white px-3 py-2 text-xs font-semibold text-blue-700 shadow-sm disabled:opacity-40" @click="selectScan">Chọn thẻ này</button>
        </div>
        <p v-else class="mt-2 text-xs text-slate-600">{{ messages[latest?.state] || 'Đang kết nối đầu đọc…' }} <code v-if="latest?.uid">{{ latest.uid }}</code></p>
      </div>
      <div v-if="selected" class="flex flex-wrap items-center gap-2 text-xs">
        <span class="text-slate-500">Đã chọn:</span><code class="rounded bg-emerald-50 px-2 py-1 font-bold text-emerald-800">{{ selected.uid }}</code>
        <span v-if="expired" class="text-amber-700">Hết hạn. Quét và chọn lại thẻ.</span>
      </div>
      <div>
        <label :for="'stock-' + cabinetId" class="text-xs font-semibold text-slate-600">2. Thiết bị từ kho</label>
        <select :id="'stock-' + cabinetId" v-model="equipmentId" :disabled="!selected || expired || busy || loading"
          class="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 disabled:bg-slate-50 disabled:text-slate-400">
          <option value="">{{ loading ? 'Đang tải kho…' : stock.length ? 'Chọn loại thiết bị' : 'Kho chưa có thiết bị phù hợp' }}</option>
          <option v-for="item in stock" :key="item.id" :value="item.id">{{ item.name }}{{ item.assetCode ? ' · ' + item.assetCode : '' }} · Còn {{ item.quantity }}</option>
        </select>
      </div>
      <button type="button" :disabled="!canSave" class="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40" @click="save">{{ busy ? 'Đang lưu…' : 'Xác nhận · Thêm 1 thiết bị vào tủ' }}</button>
      <p v-if="notice" role="status" class="text-xs text-emerald-700">{{ notice }}</p>
      <p v-if="error" role="alert" class="text-xs leading-5 text-red-700">{{ error }}</p>
    </div>
    <div class="mt-5 border-t border-slate-100 pt-4">
      <div class="flex justify-between gap-3"><h4 class="text-xs font-semibold text-slate-600">Đã gắn trong tủ</h4><button type="button" :disabled="busy" class="text-xs font-semibold text-blue-700" @click="options">Tải lại</button></div>
      <ul v-if="bindings.length" class="mt-2 divide-y divide-slate-100">
        <li v-for="tag in bindings" :key="tag.uid" class="flex flex-wrap justify-between gap-2 py-2 text-xs"><span class="text-slate-700">{{ tag.name }}</span><code class="text-slate-500">{{ tag.uid }}</code></li>
      </ul>
      <p v-else class="mt-2 text-xs text-slate-400">Chưa có thẻ nào.</p>
    </div>
  </section>
</template>
