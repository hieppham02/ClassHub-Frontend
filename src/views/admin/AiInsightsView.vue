<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import AdminPageTitle from '@/components/admin/layout/AdminPageTitle.vue'
import { api } from '@/services/apiClient.js'
const periodDays = ref(30)
const tab = ref('battery'), model = ref(null), modelError = ref(''), forecasts = ref([]), forecastError = ref('')
const predicting = ref(false), prediction = ref(null), predictError = ref(''), roomError = ref(''), roomBusy = ref(false)
const usage = ref(null), search = ref(''), usedOnly = ref(true), page = ref(1), selectedRoom = ref(null)
const form = reactive({ deviceKind: 0, ageDays: 7, borrowHoursTotal: 12, borrowEventsTotal: 16, hoursLast7: 8, activeDaysLast7: 5, rechargeable: false })
function today() { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()) }
function earlier(value, days) { const d = new Date(value + 'T00:00:00Z'); d.setUTCDate(d.getUTCDate() - days); return d.toISOString().slice(0, 10) }
const to = ref(today()), from = ref(earlier(to.value, 13))
const metrics = computed(() => model.value?.metadata?.metrics)
const featureNames = { deviceKind: 'Loại thiết bị', ageDays: 'Tuổi pin', borrowHoursTotal: 'Giờ mượn tích lũy', borrowEventsTotal: 'Số lượt nhận', hoursLast7: 'Giờ mượn 7 ngày', activeDaysLast7: 'Ngày dùng trong tuần', rechargeable: 'Pin sạc' }
const importance = computed(() => Object.entries(model.value?.metadata?.featureImportance || {}).sort((a,b) => b[1]-a[1]))
const filtered = computed(() => (usage.value?.items || []).filter(r => (!usedOnly.value || r.usedSlots > 0) && (r.roomId + ' ' + r.roomName).toLowerCase().includes(search.value.toLowerCase())).sort((a,b) => b.slotUtilizationPercent-a.slotUtilizationPercent || b.borrowCount-a.borrowCount))
const visible = computed(() => filtered.value.slice((page.value-1)*25,page.value*25))
const totalBorrows = computed(() => (usage.value?.items || []).reduce((s,r) => s+r.borrowCount,0))
const usedSlots = computed(() => (usage.value?.items || []).reduce((s,r) => s+r.usedSlots,0))
const slotPercent = computed(() => {
  const capacity = (usage.value?.items || []).reduce((s,r) => s+r.capacitySlots,0)
  return capacity ? 100*usedSlots.value/capacity : 0
})
const timePercent = computed(() => {
  const rows = usage.value?.items || [], total = rows.reduce((s,r) => s+r.capacityHours,0)
  return total ? 100*rows.reduce((s,r) => s+r.usageHours,0)/total : 0
})
watch([search, usedOnly], () => { page.value=1 })
watch(form, () => { prediction.value=null; predictError.value='' }, { deep: true })
function number(value, digits=1) { return Number(value || 0).toLocaleString('vi-VN',{maximumFractionDigits:digits}) }
function date(value) { return value ? new Date(value).toLocaleDateString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'}) : '—' }
function previousMonth() {
  const end=earlier(today().slice(0,7)+'-01',1)
  from.value=end.slice(0,7)+'-01';to.value=end;loadRooms()
}
watch(() => form.deviceKind, value => { periodDays.value=value===0?30:365 })
function priority(value) { return value==='HIGH'?'Nên kiểm tra trong 7 ngày':value==='MEDIUM'?'Lên lịch kiểm tra sớm':'Theo dõi định kỳ' }
async function predict() {
  if(predicting.value)return
  predicting.value=true; predictError.value=''; prediction.value=null
  try { prediction.value=await api.post('/admin/ai/battery/predict',{...form}) }
  catch(e) { predictError.value=e.message }
  finally { predicting.value=false }
}
function sample(kind) {
  Object.assign(form, kind===0 ? {deviceKind:0,ageDays:7,borrowHoursTotal:12,borrowEventsTotal:16,hoursLast7:8,activeDaysLast7:5,rechargeable:false} :
    kind===1 ? {deviceKind:0,ageDays:7,borrowHoursTotal:28,borrowEventsTotal:35,hoursLast7:20,activeDaysLast7:7,rechargeable:false} :
    {deviceKind:1,ageDays:100,borrowHoursTotal:80,borrowEventsTotal:150,hoursLast7:8,activeDaysLast7:5,rechargeable:false})
  predict()
}
async function loadModel() {
  try { model.value=await api.get('/admin/ai/model') } catch(e) { modelError.value=e.message }
}
async function loadForecasts() {
  try { forecasts.value=(await api.get('/admin/ai/battery/forecasts')).items } catch(e) { forecastError.value=e.message }
}
async function loadRooms() {
  if(roomBusy.value)return
  roomBusy.value=true; roomError.value=''
  try {
    usage.value=await api.get('/admin/ai/rooms?'+new URLSearchParams({from:from.value,to:to.value}))
    selectedRoom.value=null;page.value=1
  } catch(e) { roomError.value=e.message;usage.value=null }
  finally { roomBusy.value=false }
}
function downloadReport() {
  const m=model.value?.metadata
  const lines=['# ClassHub — AI dự báo pin và sử dụng phòng','',
    '## Mô hình dự báo pin','',
    'Thuật toán: Gradient Boosting Regression.','Phiên bản: '+(model.value?.modelVersion || 'Chưa tải'),
    'Nguồn huấn luyện: dữ liệu tổng hợp. Chưa xác minh độ chính xác trên pin thực tế.',
    'Số mẫu: '+(m?.sampleCount || 0),
    'MAE tập kiểm thử: '+number(metrics.value?.maeDays)+' ngày; lịch cố định: '+number(metrics.value?.baselineMaeDays)+' ngày.',
    'Mic: '+number(metrics.value?.microphoneMaeDays)+' ngày; điều khiển: '+number(metrics.value?.remoteMaeDays)+' ngày.',
    'Chia tập: '+(m?.split || ''),'',
    '## Kịch bản đang xem','',
    JSON.stringify({...form,periodDays:periodDays.value,prediction:prediction.value},null,2),'',
    '## Sử dụng phòng','',
    'Khoảng ngày: '+(usage.value?.from || '')+' đến '+(usage.value?.to || ''),
    'Lượt nhận: '+totalBorrows.value+'; ca sử dụng: '+usedSlots.value+'; tỷ lệ ca: '+number(slotPercent.value)+'%.',
    'Một phòng tối đa 5 ca/ngày. Nhiều lượt nhận trong một ca vẫn chỉ tính một ca.',
    'Thời gian nhận/trả là dữ liệu đại diện cho sử dụng; chưa chứng minh có người trong phòng.',
    'Phòng có hoạt động nhưng không đăng ký mượn: chưa triển khai.']
  const url=URL.createObjectURL(new Blob([lines.join('\n')],{type:'text/markdown;charset=utf-8'}))
  const a=document.createElement('a');a.href=url;a.download='ClassHub-AI-report.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
}
onMounted(() => { loadModel();loadForecasts();loadRooms();predict() })
</script>
<template>
  <AdminLayout>
    <div class="space-y-5 p-4 sm:p-6">
      <AdminPageTitle title="AI & sử dụng phòng" subtitle="Dự báo lịch thay pin và phân tích sử dụng theo ngữ cảnh mượn/trả." />
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex flex-wrap gap-2">
          <button class="ai-tab" :class="tab==='battery'?'bg-blue-600 text-white':'bg-white text-slate-600'" @click="tab='battery'">Dự báo pin AI</button>
          <button class="ai-tab" :class="tab==='rooms'?'bg-blue-600 text-white':'bg-white text-slate-600'" @click="tab='rooms'">Sử dụng phòng</button>
        </div>
        <button class="ai-button" @click="downloadReport">Xuất báo cáo</button>
      </div>
      <template v-if="tab==='battery'">
        <section class="ai-panel">
          <div class="flex flex-wrap items-center justify-between gap-3"><div><h2 class="font-bold text-slate-900">Dự báo thời điểm kiểm tra / thay pin</h2><p class="mt-1 text-sm text-slate-500">Gradient Boosting Regression · {{ model?.metadata?.sampleCount || '—' }} mẫu huấn luyện và đánh giá</p></div><span class="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">Nguồn huấn luyện: dữ liệu tổng hợp</span></div>
          <p class="mt-3 text-sm leading-6 text-slate-600">Mô hình học từ các chu kỳ pin tổng hợp. Giờ mượn là dữ liệu đại diện, không phải thời gian bật thiết bị. Kết quả hỗ trợ lên lịch kiểm tra, chưa thay thế đo pin thực tế.</p>
          <p v-if="modelError" role="alert" class="mt-3 text-red-600">{{ modelError }}</p>
          <div v-if="metrics" class="mt-4 grid gap-3 sm:grid-cols-3">
            <div class="ai-kpi"><p>Sai số AI trên tập kiểm thử</p><strong>{{ number(metrics.maeDays) }} ngày</strong></div>
            <div class="ai-kpi"><p>Sai số lịch cố định</p><strong>{{ number(metrics.baselineMaeDays) }} ngày</strong></div>
            <div class="ai-kpi"><p>Cải thiện so với lịch cố định</p><strong>{{ number(100*(1-metrics.maeDays/metrics.baselineMaeDays)) }}%</strong></div>
          </div>
        </section>
        <div class="grid items-start gap-5 lg:grid-cols-2">
          <section class="ai-panel">
            <h2 class="font-bold text-slate-900">Thử dự báo</h2>
            <div class="mt-3 flex flex-wrap gap-2"><button :disabled="predicting" class="ai-button" @click="sample(0)">Mic ít dùng</button><button :disabled="predicting" class="ai-button" @click="sample(1)">Mic dùng nhiều</button><button :disabled="predicting" class="ai-button" @click="sample(2)">Điều khiển</button></div>
            <form class="mt-4 grid gap-4 sm:grid-cols-2" @submit.prevent="predict">
              <label class="ai-field">Loại thiết bị<select v-model.number="form.deviceKind"><option :value="0">Mic</option><option :value="1">Điều khiển điều hòa / TV</option></select></label>
              <label class="ai-field">Ngày từ lần thay pin<input v-model.number="form.ageDays" type="number" min="0" max="730" step="0.1" required></label>
              <label class="ai-field">Tổng giờ được mượn<input v-model.number="form.borrowHoursTotal" type="number" min="0" max="17520" step="0.1" required></label>
              <label class="ai-field">Số lượt nhận thiết bị<input v-model.number="form.borrowEventsTotal" type="number" min="0" max="100000" step="1" required></label>
              <label class="ai-field">Giờ mượn trong 7 ngày<input v-model.number="form.hoursLast7" type="number" min="0" max="168" step="0.1" required></label>
              <label class="ai-field">Ngày có sử dụng trong 7 ngày<input v-model.number="form.activeDaysLast7" type="number" min="0" max="7" step="1" required></label>
              <label class="ai-field">Chu kỳ tham chiếu do người dùng đặt (ngày)<input v-model.number="periodDays" type="number" min="1" max="730" required></label>
              <label class="flex items-center gap-2 text-sm text-slate-600"><input v-model="form.rechargeable" type="checkbox"> Pin sạc</label>
              <button :disabled="predicting" class="rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50">{{ predicting?'Đang dự báo…':'Chạy mô hình AI' }}</button>
            </form>
            <p v-if="predictError" role="alert" class="mt-3 text-sm text-red-600">{{ predictError }}</p>
          </section>
          <section class="ai-panel min-h-64" aria-label="Kết quả dự báo">
            <h2 class="font-bold text-slate-900">Kết quả dự báo</h2>
            <div v-if="prediction" aria-live="polite" class="mt-4">
              <div class="rounded-2xl p-5" :class="prediction.priority==='HIGH'?'bg-amber-50':'bg-blue-50'">
                <p class="text-sm text-slate-500">Thời gian còn lại ước tính</p><p class="mt-2 text-4xl font-bold text-slate-900">{{ number(prediction.remainingDays) }} <span class="text-base font-medium text-slate-500">ngày</span></p>
                <p class="mt-3 text-sm font-semibold text-blue-800">{{ priority(prediction.priority) }}</p>
                <p class="mt-3 text-xs text-slate-600">Theo chu kỳ tham chiếu {{ periodDays }} ngày: còn {{ number(Math.max(0,periodDays-form.ageDays)) }} ngày. Dự báo AI có xét mức mượn.</p>
                <p class="mt-2 text-sm text-slate-600">Mốc tham khảo: {{ date(prediction.suggestedDateUtc) }}</p>
                <p class="mt-2 text-xs text-slate-500">Khoảng tham khảo: {{ number(prediction.lowerDays) }}–{{ number(prediction.upperDays) }} ngày. Khoảng sai số được hiệu chỉnh trên dữ liệu tổng hợp.</p>
              </div>
              <p v-if="prediction.outsideTrainingRange" class="mt-3 text-xs text-amber-700">Có đầu vào ngoài phạm vi dữ liệu huấn luyện; cần kiểm tra thực tế.</p>
              <p class="mt-3 break-all text-xs text-slate-400">Phiên bản mô hình: {{ prediction.modelVersion }}</p>
            </div>
            <p v-else class="mt-8 text-center text-sm text-slate-400">Chọn kịch bản hoặc nhập thông số để chạy dự báo.</p>
          </section>
        </div>
        <section class="ai-panel">
          <h2 class="font-bold text-slate-900">Dự báo từ hồ sơ thiết bị</h2>
          <p class="mt-2 text-sm text-slate-500">Tính tuổi pin từ lần thay/sạc hoàn tất và mức mượn tích lũy. Không tự tạo lịch sử thay pin.</p>
          <p v-if="forecastError" role="alert" class="mt-3 text-sm text-red-600">{{ forecastError }}</p>
          <p v-else-if="!forecasts.length" class="mt-3 rounded-lg bg-slate-50 p-4 text-sm text-slate-600">Chưa có hồ sơ pin. <RouterLink to="/admin/batteries" class="font-semibold text-blue-700">Thêm hồ sơ và lần thay pin</RouterLink> để dự báo theo thiết bị. Kịch bản thử ở trên vẫn chạy được ngay.</p>
          <ul v-else class="mt-3 divide-y divide-slate-100"><li v-for="p in forecasts" :key="p.id" class="flex flex-wrap justify-between gap-3 py-3 text-sm"><span><b>{{ p.assetCode }}</b> · {{ p.name }} · {{ p.room || 'Kho' }}</span><span v-if="p.forecast" class="font-semibold text-blue-700">{{ number(p.forecast.remainingDays) }} ngày · {{ date(p.forecast.suggestedDateUtc) }}</span><span v-else class="text-amber-700">{{ p.message }}</span></li></ul>
        </section>
        <details class="ai-panel text-sm text-slate-600"><summary class="cursor-pointer font-semibold">Mô hình đã học gì?</summary><p class="mt-3">Mức đóng góp trên toàn bộ mô hình; không phải giải thích nhân quả cho một thiết bị.</p><div v-for="[key,value] in importance" :key="key" class="mt-3"><div class="flex justify-between text-xs"><span>{{ featureNames[key] }}</span><span>{{ number(value*100) }}%</span></div><div class="mt-1 h-2 rounded bg-slate-100"><div class="h-2 rounded bg-blue-500" :style="{width:(value*100)+'%'}"></div></div></div><p class="mt-4 text-xs">Tách tập theo thiết bị, không dùng cùng thiết bị cho huấn luyện và kiểm thử. Sai số mic: {{ number(metrics?.microphoneMaeDays) }} ngày; điều khiển: {{ number(metrics?.remoteMaeDays) }} ngày. Các số này chỉ áp dụng tập tổng hợp.</p></details>
      </template>
      <template v-else>
        <section class="ai-panel">
          <h2 class="font-bold text-slate-900">Tần suất & tỷ lệ sử dụng phòng</h2>
          <p class="mt-2 text-sm leading-6 text-slate-500">Khả dụng quy ước 5 ca/phòng/ngày trong khoảng đã chọn. Nhiều lượt nhận trong cùng ca chỉ tính một ca; chuyển phòng tính riêng từng phòng. Khoảng thời gian chồng nhau được hợp nhất.</p>
          <form class="mt-4 flex flex-wrap items-end gap-3" @submit.prevent="loadRooms"><label class="ai-field">Từ ngày<input v-model="from" type="date" required></label><label class="ai-field">Đến ngày<input v-model="to" type="date" :max="today()" required></label><button :disabled="roomBusy" class="ai-button">{{ roomBusy?'Đang tính…':'Xem thống kê' }}</button></form>
          <button type="button" :disabled="roomBusy" class="ai-button mt-3" @click="previousMonth">Xem tháng trước</button>
          <p v-if="roomError" role="alert" class="mt-3 text-sm text-red-600">{{ roomError }}</p>
          <div v-if="usage" class="mt-4 grid gap-3 sm:grid-cols-4"><div class="ai-kpi"><p>Lượt nhận thiết bị</p><strong>{{ number(totalBorrows,0) }}</strong></div><div class="ai-kpi"><p>Ca có sử dụng</p><strong>{{ number(usedSlots,0) }}</strong></div><div class="ai-kpi"><p>Tỷ lệ sử dụng ca</p><strong>{{ number(slotPercent) }}%</strong></div><div class="ai-kpi"><p>Tỷ lệ sử dụng thời gian</p><strong>{{ number(timePercent) }}%</strong></div></div>
          <p class="mt-3 text-xs text-slate-500">Thống kê từ thời điểm nhận/trả đã lưu trong hệ thống. Phòng không có bản ghi không đồng nghĩa phòng trống. Tìm phòng có sử dụng nhưng không đăng ký: chưa triển khai.</p>
        </section>
        <section v-if="usage" class="ai-panel">
          <div class="flex flex-wrap items-center gap-4"><input v-model="search" class="rounded-lg border border-slate-200 px-3 py-2 text-sm" placeholder="Tìm phòng"><label class="flex items-center gap-2 text-sm"><input v-model="usedOnly" type="checkbox"> Chỉ phòng có sử dụng</label><span class="text-xs text-slate-400">{{ filtered.length }}/{{ usage.roomCount }} phòng</span></div>
          <div class="mt-4 overflow-x-auto"><table class="w-full text-left text-sm"><thead class="bg-slate-50 text-xs text-slate-500"><tr><th class="p-3">Phòng</th><th class="p-3">Lượt nhận</th><th class="p-3">Ca sử dụng / khả dụng</th><th class="p-3">Giờ sử dụng</th><th class="p-3">Tỷ lệ ca</th></tr></thead><tbody><tr v-for="r in visible" :key="r.roomId" class="border-b border-slate-100"><td class="p-3"><button class="font-semibold text-blue-700 hover:underline" @click="selectedRoom=r">{{ r.roomName || r.roomId }}</button><p class="text-xs text-slate-400">{{ r.roomId }}</p></td><td class="p-3">{{ r.borrowCount }}</td><td class="p-3">{{ r.usedSlots }}/{{ r.capacitySlots }}</td><td class="p-3">{{ number(r.usageHours) }}</td><td class="p-3"><div class="h-2 w-24 rounded bg-slate-100"><div class="h-2 rounded bg-emerald-500" :style="{width:r.slotUtilizationPercent+'%'}"></div></div><span class="mt-1 block text-xs">{{ number(r.slotUtilizationPercent) }}%</span></td></tr></tbody></table></div>
          <p v-if="!filtered.length" class="py-6 text-center text-sm text-slate-500">Chưa có dữ liệu sử dụng trong khoảng ngày hoặc bộ lọc này.</p>
          <div class="mt-4 flex items-center justify-between text-sm"><button :disabled="page===1" class="ai-button" @click="page--">Trước</button><span>Trang {{ page }}/{{ Math.max(1,Math.ceil(filtered.length/25)) }}</span><button :disabled="page*25>=filtered.length" class="ai-button" @click="page++">Sau</button></div>
        </section>
        <section v-if="selectedRoom" class="ai-panel"><h2 class="font-bold">{{ selectedRoom.roomName }} · Theo ngày / ca</h2><div class="mt-4 overflow-x-auto"><table class="w-full text-left text-sm"><thead><tr class="text-xs text-slate-500"><th class="p-2">Ngày</th><th v-for="i in 5" :key="i" class="p-2">Ca {{ i }}</th><th class="p-2">Lượt nhận</th></tr></thead><tbody><tr v-for="day in selectedRoom.daily" :key="day.date"><td class="p-2">{{ day.date }}</td><td v-for="slot in day.slots" :key="slot.id" class="p-2"><span class="block rounded px-3 py-2 text-center text-xs" :class="slot.used?'bg-emerald-100 text-emerald-800':'bg-slate-50 text-slate-400'" :title="slot.name">{{ slot.used?'Có sử dụng':'—' }}</span></td><td class="p-2">{{ day.borrowCount }}</td></tr></tbody></table></div></section>
      </template>
    </div>
  </AdminLayout>
</template>
<style scoped>
@reference "../../style.css";
.ai-panel { @apply rounded-2xl border border-blue-100 bg-white p-4 sm:p-5; }
.ai-tab { @apply rounded-xl border border-blue-100 px-4 py-2.5 text-sm font-semibold; }
.ai-button { @apply rounded-lg border border-blue-200 bg-white px-3 py-2 text-sm font-semibold text-blue-700 disabled:opacity-40; }
.ai-field { @apply flex flex-col gap-2 text-xs font-semibold text-slate-600; }
.ai-field input, .ai-field select { @apply min-h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm font-normal text-slate-800; }
.ai-kpi { @apply rounded-xl bg-slate-50 p-4; }
.ai-kpi p { @apply text-xs text-slate-500; }
.ai-kpi strong { @apply mt-2 block text-2xl font-bold text-slate-900; }
</style>
