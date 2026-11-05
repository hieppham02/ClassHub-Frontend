<script setup>
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import AdminPageTitle from '@/components/admin/layout/AdminPageTitle.vue'
import AppModal from '@/components/shared/AppModal.vue'
import { api } from '@/services/apiClient.js'

const base = '/admin/batteries'
const items = ref([]), total = ref(0), page = ref(1), listLoading = ref(false)
const options = ref({ equipment: [], tags: [] }), optionsReady = ref(false)
const search = ref(''), room = ref(''), priority = ref(''), includeDisabled = ref(false)
const error = ref(''), success = ref(''), detailError = ref(''), selected = ref(null), detailLoading = ref(false)
const busy = ref(false), needsReload = ref(false), inspections = ref([]), services = ref([])
const inspectionBefore = ref(null), serviceBefore = ref(null), historyLoading = ref(false)
const freshHours = ref(168), assessedAt = ref('')
let listEpoch = 0, detailEpoch = 0, optionsEpoch = 0
const modal = ref(false), editing = ref(false), formError = ref(''), profileNeedsReload = ref(false)
const profileForm = reactive({})
const inspection = reactive({}), service = reactive({})
const labels = {
  HIGH: 'Ưu tiên cao', MEDIUM: 'Cần kiểm tra', LOW: 'Bình thường', UNKNOWN: 'Chưa đủ thông tin',
  GOOD: 'Pin tốt', EMPTY: 'Hết pin', NORMAL: 'Hoạt động bình thường', INTERMITTENT: 'Chập chờn',
  NOT_WORKING: 'Không hoạt động', STILL_FAULTY: 'Vẫn còn lỗi',
  REPLACE_BATTERY: 'Thay pin', RECHARGE: 'Sạc pin', CHECK: 'Kiểm tra', REPAIR: 'Sửa chữa',
  BATTERY: 'Do pin', DEVICE: 'Do thiết bị'
}
const label = value => labels[value] || value
const batteryLabel = value => value === 'LOW' ? 'Pin yếu' : value === 'UNKNOWN' ? 'Chưa kiểm tra pin' : label(value)
const outcomeLabel = value => value === 'UNKNOWN' ? 'Chưa xác nhận kết quả' : label(value)
function date(value) { return value ? new Date(value).toLocaleString('vi-VN') : '—' }
function localNow() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}
function instant(value) {
  const d = new Date(value)
  if (!value || !Number.isFinite(d.getTime())) throw new Error('Chọn thời điểm hợp lệ.')
  return d.toISOString()
}
const pages = computed(() => Math.max(1, Math.ceil(total.value / 25)))
const rooms = computed(() => [...new Set(options.value.equipment.map(e => e.roomId).filter(Boolean))].sort())
const tagOptions = computed(() => options.value.tags.filter(t =>
  t.equipmentId === Number(profileForm.equipmentId) && (!t.profileId || t.profileId === selected.value?.profile.id)))
const chosenEquipment = computed(() => options.value.equipment.find(e => e.id === Number(profileForm.equipmentId)))
const equipmentOptions = computed(() => options.value.equipment.filter(e =>
  e.registeredCount < e.quantity || editing.value && e.id === Number(profileForm.equipmentId)))
function badge(value) {
  return value === 'HIGH' ? 'bg-red-50 text-red-700' : value === 'MEDIUM' ? 'bg-amber-50 text-amber-800' :
    value === 'LOW' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'
}
async function loadOptions() {
  const epoch = ++optionsEpoch
  try {
    const data = await api.get(base + '/options')
    if (epoch === optionsEpoch) { options.value = data; optionsReady.value = true }
  } catch (err) { if (epoch === optionsEpoch) { optionsReady.value = false; error.value = err.message } }
}
async function loadList(newPage = 1) {
  const epoch = ++listEpoch
  listLoading.value = true; error.value = ''; page.value = newPage
  const query = new URLSearchParams({ page: String(newPage), includeDisabled: String(includeDisabled.value) })
  if (search.value.trim()) query.set('search', search.value.trim())
  if (room.value) query.set('room', room.value)
  if (priority.value) query.set('priority', priority.value)
  try {
    const data = await api.get(base + '?' + query)
    if (epoch !== listEpoch) return
    items.value = data.items; total.value = data.total
    freshHours.value = data.inspectionFreshHours; assessedAt.value = data.assessedAtUtc
  } catch (err) { if (epoch === listEpoch) { items.value = []; total.value = 0; error.value = err.message } }
  finally { if (epoch === listEpoch) listLoading.value = false }
}
function resetEntryForms(profile) {
  Object.assign(inspection, { at: localNow(), batteryState: 'UNKNOWN', operationState: 'UNKNOWN',
    voltageV: '', batteryPercent: '', measurementMethod: '', symptomCode: '', note: '', sessionId: '' })
  Object.assign(service, { at: localNow(), action: 'REPLACE_BATTERY', batteryType: profile.batteryType || '',
    batteryCount: profile.batteryCount ?? '', rechargeCompleted: '', outcome: 'UNKNOWN', confirmedCause: 'UNKNOWN', note: '' })
}
async function loadDetail(id) {
  if (busy.value) return
  const epoch = ++detailEpoch
  selected.value = null; detailLoading.value = true; detailError.value = ''; needsReload.value = true
  inspections.value = []; services.value = []
  try {
    const [detail, checks, work] = await Promise.all([
      api.get(base + '/' + id), api.get(base + '/' + id + '/inspections'), api.get(base + '/' + id + '/services')
    ])
    if (epoch !== detailEpoch) return
    selected.value = detail; inspections.value = checks.items; services.value = work.items
    inspectionBefore.value = checks.nextBefore; serviceBefore.value = work.nextBefore
    resetEntryForms(detail.profile); needsReload.value = false
  } catch (err) { if (epoch === detailEpoch) detailError.value = err.message }
  finally { if (epoch === detailEpoch) detailLoading.value = false }
}
async function moreHistory(kind) {
  if (!selected.value || historyLoading.value || busy.value) return
  const id = selected.value.profile.id, epoch = detailEpoch
  const cursor = kind === 'inspections' ? inspectionBefore.value : serviceBefore.value
  if (!cursor) return
  historyLoading.value = true
  try {
    const data = await api.get(base + '/' + id + '/' + kind + '?before=' + cursor)
    if (epoch !== detailEpoch) return
    if (kind === 'inspections') { inspections.value.push(...data.items); inspectionBefore.value = data.nextBefore }
    else { services.value.push(...data.items); serviceBefore.value = data.nextBefore }
  } catch (err) { if (epoch === detailEpoch) detailError.value = err.message }
  finally { historyLoading.value = false }
}
function openProfile(edit = false) {
  if (busy.value || !optionsReady.value || edit && !selected.value) return
  loadOptions()
  editing.value = edit; formError.value = ''; profileNeedsReload.value = false
  const p = edit ? selected.value.profile : {}
  Object.assign(profileForm, { equipmentId: p.equipmentId || '', assetCode: p.assetCode || '',
    currentRfidTagId: p.currentRfidTagId ?? '', batteryType: p.batteryType || '', batteryCount: p.batteryCount ?? '',
    rechargeable: p.rechargeable === true ? 'true' : p.rechargeable === false ? 'false' : '',
    manufacturer: p.manufacturer || '', model: p.model || '', enabled: p.enabled ?? true, version: p.version || 1 })
  modal.value = true
}
async function saveProfile() {
  if (busy.value || profileNeedsReload.value) return
  busy.value = true; formError.value = ''; success.value = ''
  let result
  try {
    const body = { ...profileForm, equipmentId: Number(profileForm.equipmentId),
      currentRfidTagId: profileForm.currentRfidTagId === '' ? null : Number(profileForm.currentRfidTagId),
      batteryCount: profileForm.batteryCount === '' ? null : Number(profileForm.batteryCount),
      rechargeable: profileForm.rechargeable === '' ? null : profileForm.rechargeable === 'true' }
    result = editing.value ? await api.put(base + '/' + selected.value.profile.id, body) : await api.post(base, body)
    modal.value = false; success.value = 'Đã lưu hồ sơ micro.'
  } catch (err) {
    formError.value = err.message + ' Nếu mất kết nối, đóng biểu mẫu và tải lại danh sách để kiểm tra trước khi gửi lại.'
    needsReload.value = true; profileNeedsReload.value = true
  } finally { busy.value = false }
  if (result) await Promise.all([loadOptions(), loadList(page.value), loadDetail(result.profile.id)])
}
const nullableNumber = value => value === '' || value == null ? null : Number(value)
async function saveEntry(kind) {
  if (busy.value || needsReload.value || !selected.value?.profile.enabled) return
  const p = selected.value.profile
  busy.value = true; detailError.value = ''; success.value = ''
  let saved = false
  try {
    const body = kind === 'inspections' ? {
      version: p.version, observedAt: instant(inspection.at), batteryState: inspection.batteryState,
      operationState: inspection.operationState, voltageV: nullableNumber(inspection.voltageV),
      batteryPercent: nullableNumber(inspection.batteryPercent), measurementMethod: inspection.measurementMethod,
      symptomCode: inspection.symptomCode, note: inspection.note, sessionId: nullableNumber(inspection.sessionId)
    } : {
      version: p.version, performedAt: instant(service.at), action: service.action, batteryType: service.batteryType,
      batteryCount: nullableNumber(service.batteryCount), rechargeCompleted: service.action === 'RECHARGE' && service.rechargeCompleted !== '' ?
        service.rechargeCompleted === 'true' : null, outcome: service.outcome, confirmedCause: service.confirmedCause, note: service.note
    }
    await api.post(base + '/' + p.id + '/' + kind, body)
    saved = true; success.value = 'Đã lưu kết quả và cập nhật mức ưu tiên.'
  } catch (err) {
    detailError.value = err.message + ' Tải lại hồ sơ và kiểm tra lịch sử trước khi gửi lại.'
    needsReload.value = true
  } finally { busy.value = false }
  if (saved) await Promise.all([loadList(page.value), loadDetail(p.id)])
}
onMounted(() => { loadOptions(); loadList() })
onUnmounted(() => { listEpoch++; detailEpoch++; optionsEpoch++ })
</script>

<template>
  <AdminLayout>
    <div class="mx-auto max-w-7xl space-y-5 p-4 pb-24 sm:p-7 sm:pb-8">
      <header class="flex flex-wrap items-center justify-between gap-4">
        <AdminPageTitle eyebrow="Cơ sở vật chất" title="Theo dõi pin micro" />
        <button class="primary" :disabled="busy || !optionsReady" @click="openProfile()">Thêm micro theo dõi</button>
      </header>
      <p class="text-sm text-slate-500">Ưu tiên kiểm tra theo kết quả đã ghi nhận. Dự báo AI nằm ở mục AI & sử dụng phòng.</p>
      <p v-if="success" role="status" class="notice good">{{ success }}</p>
      <p v-if="error" role="alert" class="notice bad">{{ error }}</p>
      <section class="panel">
        <form class="flex flex-wrap items-end gap-3" @submit.prevent="loadList()">
          <label class="field grow">Tìm micro hoặc RFID<input v-model="search" maxlength="80" placeholder="Mã micro, tên thiết bị, UID"></label>
          <label class="field">Phòng<select v-model="room"><option value="">Tất cả phòng và kho</option><option v-for="id in rooms" :key="id" :value="id">{{ id }}</option></select></label>
          <label class="field">Mức ưu tiên<select v-model="priority"><option value="">Tất cả</option><option v-for="value in ['HIGH','MEDIUM','UNKNOWN','LOW']" :key="value" :value="value">{{ label(value) }}</option></select></label>
          <button class="secondary" :disabled="listLoading || busy">Lọc / Làm mới</button>
          <label class="flex items-center gap-2 text-sm"><input v-model="includeDisabled" type="checkbox"> Cả ngừng theo dõi</label>
        </form>
        <p class="mt-3 text-xs text-slate-500">Kiểm tra có hiệu lực {{ freshHours }} giờ. Đánh giá lúc {{ date(assessedAt) }}.</p>
        <div v-if="listLoading" role="status" class="py-8 text-center text-slate-500">Đang tải hồ sơ…</div>
        <div v-else-if="!items.length" class="py-8 text-center">
          <p class="font-semibold">Chưa có micro trong phạm vi này</p>
          <p class="mt-1 text-sm text-slate-500">Thêm hồ sơ cho từng chiếc micro đã kiểm kê. Không có hồ sơ chưa có nghĩa thiết bị đang tốt.</p>
          <RouterLink to="/admin/assets" class="mt-3 inline-block text-sm text-blue-700">Mở danh mục tài sản</RouterLink>
        </div>
        <div v-else class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <button v-for="row in items" :key="row.profile.id" type="button" :disabled="busy"
            class="rounded-xl border p-4 text-left hover:border-blue-400 disabled:opacity-60"
            :class="selected?.profile.id === row.profile.id ? 'border-blue-500 bg-blue-50/40' : 'border-slate-200'"
            @click="loadDetail(row.profile.id)">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <strong>{{ row.profile.assetCode }}</strong><span :class="badge(row.assessment.priority)" class="rounded-full px-2 py-1 text-xs font-semibold">{{ label(row.assessment.priority) }}</span>
            </div>
            <p class="mt-2 text-sm">{{ row.equipmentName }} · {{ row.roomId || 'Kho' }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ row.uid ? 'RFID ' + row.uid : 'Chưa liên kết thẻ' }}{{ row.profile.enabled ? '' : ' · Ngừng theo dõi' }}</p>
            <p class="mt-3 text-sm">{{ row.assessment.reason }}</p>
          </button>
        </div>
        <div class="mt-4 flex items-center justify-between gap-3 text-sm">
          <span>{{ total }} micro · Trang {{ page }}/{{ pages }}</span>
          <div class="flex gap-2"><button class="secondary" :disabled="page <= 1 || listLoading || busy" @click="loadList(page-1)">Trước</button><button class="secondary" :disabled="page >= pages || listLoading || busy" @click="loadList(page+1)">Sau</button></div>
        </div>
      </section>
      <p v-if="detailLoading" role="status" class="panel">Đang tải lịch sử micro…</p>
      <p v-if="detailError" role="alert" class="notice bad">{{ detailError }}</p>
      <section v-if="selected" class="panel space-y-5">
        <header class="flex flex-wrap items-start justify-between gap-3">
          <div><h2 class="text-lg font-bold">{{ selected.profile.assetCode }} · {{ selected.equipmentName }}</h2>
            <p class="mt-1 text-sm text-slate-500">{{ selected.roomId || 'Kho' }} · {{ selected.profile.batteryType || 'Chưa rõ loại pin' }} · {{ selected.profile.batteryCount ? selected.profile.batteryCount + ' viên' : 'Chưa rõ số viên' }}</p>
            <p class="mt-1 text-xs text-slate-500">RFID: {{ selected.uid || 'Chưa liên kết' }} · {{ selected.profile.manufacturer || 'Chưa rõ hãng' }} {{ selected.profile.model || '' }}</p>
          </div>
          <div class="flex gap-2"><button class="secondary" :disabled="busy" @click="loadDetail(selected.profile.id)">Tải lại hồ sơ</button><button class="secondary" :disabled="busy || !optionsReady" @click="openProfile(true)">Sửa hồ sơ</button></div>
        </header>
        <div class="rounded-xl p-4" :class="badge(selected.assessment.priority)">
          <strong>{{ label(selected.assessment.priority) }}</strong><p class="mt-1 text-sm">{{ selected.assessment.reason }}</p>
          <p class="mt-1 text-sm">{{ selected.assessment.recommendedAction }}</p>
          <p class="mt-2 text-xs">Bằng chứng: {{ date(selected.assessment.evidenceAtUtc) }}<span v-if="selected.assessment.validUntilUtc"> · Cần kiểm tra lại trước {{ date(selected.assessment.validUntilUtc) }}</span></p>
        </div>
        <p v-if="!selected.profile.enabled" class="text-sm text-slate-500">Hồ sơ đã ngừng theo dõi. Bật lại trong “Sửa hồ sơ” để ghi kết quả mới.</p>
        <p v-if="needsReload" class="text-sm text-amber-800">Tải lại hồ sơ và kiểm tra lịch sử trước khi gửi thêm kết quả.</p>
        <div class="grid gap-5 lg:grid-cols-2">
          <form class="rounded-xl border border-slate-200 p-4" @submit.prevent="saveEntry('inspections')">
            <h3 class="mb-4 font-bold">Ghi kiểm tra</h3>
            <fieldset :disabled="busy || needsReload || !selected.profile.enabled" class="grid gap-3 sm:grid-cols-2">
              <label class="field sm:col-span-2">Thời điểm kiểm tra (giờ máy của bạn)<input v-model="inspection.at" type="datetime-local" required></label>
              <label class="field">Tình trạng pin<select v-model="inspection.batteryState"><option v-for="v in ['UNKNOWN','GOOD','LOW','EMPTY']" :key="v" :value="v">{{ batteryLabel(v) }}</option></select></label>
              <label class="field">Hoạt động<select v-model="inspection.operationState"><option value="UNKNOWN">Chưa thử hoạt động</option><option v-for="v in ['NORMAL','INTERMITTENT','NOT_WORKING']" :key="v" :value="v">{{ label(v) }}</option></select></label>
              <label class="field">Điện áp đo được (V, nếu có)<input v-model="inspection.voltageV" type="number" min="0" max="99999.999" step="0.001"></label>
              <label class="field">Pin hiển thị (%, nếu có)<input v-model="inspection.batteryPercent" type="number" min="0" max="100" step="0.01"></label>
              <label class="field sm:col-span-2">Cách đo / nguồn thông số<input v-model="inspection.measurementMethod" maxlength="80" :required="inspection.voltageV !== '' || inspection.batteryPercent !== ''" placeholder="Ví dụ: đồng hồ đo cả bộ pin; màn hình micro"></label>
              <label class="field">Mã biểu hiện (nếu có)<input v-model="inspection.symptomCode" maxlength="50" placeholder="Ví dụ: AUDIO_DROPOUT"></label>
              <label class="field">Mã phiên tham chiếu (nếu có)<input v-model="inspection.sessionId" type="number" min="1" max="2147483647" step="1"></label>
              <label class="field sm:col-span-2">Ghi chú<textarea v-model="inspection.note" maxlength="2000" rows="2"></textarea></label>
              <button class="primary sm:col-span-2">{{ busy ? 'Đang lưu…' : 'Lưu kiểm tra' }}</button>
            </fieldset>
          </form>
          <form class="rounded-xl border border-slate-200 p-4" @submit.prevent="saveEntry('services')">
            <h3 class="mb-4 font-bold">Ghi thay pin / xử lý</h3>
            <fieldset :disabled="busy || needsReload || !selected.profile.enabled" class="grid gap-3 sm:grid-cols-2">
              <label class="field sm:col-span-2">Thời điểm xử lý (giờ máy của bạn)<input v-model="service.at" type="datetime-local" required></label>
              <label class="field">Thao tác<select v-model="service.action"><option v-for="v in ['REPLACE_BATTERY','RECHARGE','CHECK','REPAIR']" :key="v" :value="v">{{ label(v) }}</option></select></label>
              <label class="field">Kết quả sau xử lý<select v-model="service.outcome"><option v-for="v in ['UNKNOWN','NORMAL','STILL_FAULTY']" :key="v" :value="v">{{ outcomeLabel(v) }}</option></select></label>
              <label class="field">Loại pin sử dụng<input v-model="service.batteryType" maxlength="80" placeholder="Chưa rõ thì để trống"></label>
              <label class="field">Số viên pin<input v-model="service.batteryCount" type="number" min="1" max="100" step="1"></label>
              <label v-if="service.action === 'RECHARGE'" class="field sm:col-span-2">Xác nhận sạc đầy<select v-model="service.rechargeCompleted"><option value="">Chưa xác nhận</option><option value="true">Đã sạc đầy</option><option value="false">Chưa sạc đầy</option></select></label>
              <label class="field sm:col-span-2">Nguyên nhân đã xác nhận<select v-model="service.confirmedCause"><option value="UNKNOWN">Chưa xác định</option><option value="BATTERY">Do pin</option><option value="DEVICE">Do thiết bị</option></select></label>
              <label class="field sm:col-span-2">Ghi chú<textarea v-model="service.note" maxlength="2000" rows="2"></textarea></label>
              <p class="sm:col-span-2 text-xs text-slate-500">Chỉ bắt đầu chu kỳ pin mới khi thay pin hoặc sạc đầy và xác nhận hoạt động bình thường.</p>
              <button class="primary sm:col-span-2">{{ busy ? 'Đang lưu…' : 'Lưu kết quả xử lý' }}</button>
            </fieldset>
          </form>
        </div>
        <div class="grid gap-5 lg:grid-cols-2">
          <section><h3 class="mb-3 font-bold">Lịch sử kiểm tra</h3><p v-if="!inspections.length" class="text-sm text-slate-500">Chưa có kiểm tra được ghi nhận.</p>
            <ul class="space-y-3"><li v-for="entry in inspections" :key="entry.id" class="history-row">
              <p class="text-xs text-slate-500">{{ date(entry.observedAtUtc) }} · #{{ entry.id }}</p>
              <p>{{ batteryLabel(entry.batteryState) }} · {{ entry.operationState === 'UNKNOWN' ? 'Chưa thử hoạt động' : label(entry.operationState) }}</p>
              <p v-if="entry.voltageV != null || entry.batteryPercent != null" class="text-xs">{{ entry.voltageV != null ? entry.voltageV + ' V · ' : '' }}{{ entry.batteryPercent != null ? entry.batteryPercent + '% · ' : '' }}{{ entry.measurementMethod }}</p>
              <p v-if="entry.symptomCode" class="text-xs">{{ entry.symptomCode }}</p><p v-if="entry.note" class="whitespace-pre-wrap text-sm">{{ entry.note }}</p>
            </li></ul><button v-if="inspectionBefore" class="secondary mt-3" :disabled="historyLoading || busy" @click="moreHistory('inspections')">Xem kiểm tra cũ hơn</button>
          </section>
          <section><h3 class="mb-3 font-bold">Lịch sử xử lý</h3><p v-if="!services.length" class="text-sm text-slate-500">Chưa có xử lý được ghi nhận.</p>
            <ul class="space-y-3"><li v-for="entry in services" :key="entry.id" class="history-row">
              <p class="text-xs text-slate-500">{{ date(entry.performedAtUtc) }} · #{{ entry.id }}</p>
              <p>{{ label(entry.action) }} · {{ outcomeLabel(entry.outcome) }}</p>
              <p class="text-xs">{{ entry.confirmedCause === 'UNKNOWN' ? 'Chưa xác định nguyên nhân' : label(entry.confirmedCause) }}<span v-if="entry.batteryType"> · {{ entry.batteryType }}</span><span v-if="entry.batteryCount"> · {{ entry.batteryCount }} viên</span></p>
              <p v-if="entry.action === 'RECHARGE'" class="text-xs">{{ entry.rechargeCompleted === true ? 'Đã xác nhận sạc đầy' : 'Chưa xác nhận sạc đầy' }}</p>
              <p v-if="entry.note" class="whitespace-pre-wrap text-sm">{{ entry.note }}</p>
            </li></ul><button v-if="serviceBefore" class="secondary mt-3" :disabled="historyLoading || busy" @click="moreHistory('services')">Xem xử lý cũ hơn</button>
          </section>
        </div>
      </section>
      <AppModal v-if="modal" size="lg" :busy="busy" :title="editing ? 'Sửa hồ sơ micro' : 'Thêm micro theo dõi'" @close="!busy && (modal = false)">
        <form class="space-y-4" @submit.prevent="saveProfile">
          <p v-if="formError" role="alert" class="notice bad">{{ formError }}</p>
          <p class="text-sm text-slate-500">Mỗi hồ sơ là một chiếc micro đã kiểm kê. Không tự tạo thẻ hoặc thay đổi số lượng tài sản.</p>
          <fieldset :disabled="busy" class="grid gap-3 sm:grid-cols-2">
            <label class="field sm:col-span-2">Thiết bị micro trong danh mục<select v-model="profileForm.equipmentId" :disabled="editing" required @change="profileForm.currentRfidTagId = ''"><option value="">Chọn micro</option><option v-for="e in equipmentOptions" :key="e.id" :value="e.id">{{ e.name }} · {{ e.roomId || 'Kho' }} · {{ e.registeredCount }}/{{ e.quantity }} hồ sơ</option></select></label>
            <p v-if="!equipmentOptions.length" class="sm:col-span-2 text-sm text-amber-800">Chưa có thiết bị tủ còn chỗ đăng ký. Thêm hoặc kiểm kê micro tại Quản lý tài sản trước.</p>
            <label class="field">Mã riêng của chiếc micro<input v-model="profileForm.assetCode" required maxlength="80" pattern="[A-Za-z0-9_-]{1,80}" placeholder="MIC-001"></label>
            <label class="field">RFID (không bắt buộc)<select v-model="profileForm.currentRfidTagId"><option value="">Chưa liên kết</option><option v-for="tag in tagOptions" :key="tag.id" :value="tag.id">{{ tag.uid }}</option></select></label>
            <p v-if="chosenEquipment && !tagOptions.length" class="sm:col-span-2 text-xs text-slate-500">Chưa có thẻ khả dụng cho nhóm thiết bị này. Có thể tạo hồ sơ trước và liên kết thẻ sau.</p>
            <label class="field">Loại pin<input v-model="profileForm.batteryType" maxlength="80" placeholder="Ví dụ: AA alkaline"></label>
            <label class="field">Số viên pin<input v-model="profileForm.batteryCount" type="number" min="1" max="100" step="1"></label>
            <label class="field sm:col-span-2">Khả năng sạc<select v-model="profileForm.rechargeable"><option value="">Chưa rõ</option><option value="true">Pin sạc</option><option value="false">Pin không sạc</option></select></label>
            <label class="field">Hãng<input v-model="profileForm.manufacturer" maxlength="100"></label>
            <label class="field">Model<input v-model="profileForm.model" maxlength="100"></label>
            <label class="flex items-center gap-2 text-sm sm:col-span-2"><input v-model="profileForm.enabled" type="checkbox"> Đang theo dõi</label>
            <button class="primary sm:col-span-2" :disabled="profileNeedsReload || (needsReload && editing)">{{ busy ? 'Đang lưu…' : 'Lưu hồ sơ' }}</button>
          </fieldset>
          <button type="button" class="secondary" :disabled="busy" @click="modal = false">Đóng</button>
        </form>
      </AppModal>
    </div>
  </AdminLayout>
</template>

<style scoped>
@reference "../../style.css";
.panel { @apply rounded-2xl border border-blue-100 bg-white p-4 sm:p-5; }
.field { @apply flex flex-col gap-1 text-sm text-slate-600; }
.field input, .field select, .field textarea { @apply min-w-0 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900; }
.field input:focus, .field select:focus, .field textarea:focus { @apply outline-2 outline-blue-400; }
.primary { @apply rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-50; }
.secondary { @apply rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50; }
.notice { @apply rounded-xl border p-3 text-sm; }
.good { @apply border-emerald-200 bg-emerald-50 text-emerald-800; }
.bad { @apply border-red-200 bg-red-50 text-red-800; }
.history-row { @apply space-y-1 rounded-xl border border-slate-100 bg-slate-50/50 p-3; }
</style>
