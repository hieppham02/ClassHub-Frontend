<script setup>
import AppModal from '@/components/shared/AppModal.vue'
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import AdminPageTitle from '@/components/admin/layout/AdminPageTitle.vue'
import TablePagination from '@/components/shared/TablePagination.vue'
import { usePagination } from '@/composables/usePagination.js'
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '@/services/apiClient.js'
import { buildStatisticsTimeline, timelineTicks } from '@/utils/statisticsTimeline.js'

const showFilterModal = ref(false)
const isLoading = ref(true)
const errorMessage = ref('')
const activeSection = ref('overview')
const chartGranularity = ref('auto')

const activeFilters = reactive({
  groupBy: 'room',
  dateFrom: '',
  dateTo: ''
})

const tempFilters = reactive({
  groupBy: 'room',
  dateFrom: '',
  dateTo: ''
})

const isInvalidDateRange = computed(() => Boolean(
  tempFilters.dateFrom && tempFilters.dateTo && tempFilters.dateFrom > tempFilters.dateTo
))

const rawData = ref([])

const completedStatuses = new Set(['COMPLETED'])
const lateStatuses = new Set(['OVERDUE', 'EXPIRED', 'FAULT'])

const normalizedData = computed(() => rawData.value.map(item => ({
  ...item,
  user: item.borrower || item.borrowerId || 'Không xác định',
  statusLabel: getStatusLabel(item.status),
  onTime: completedStatuses.has(item.status),
  late: lateStatuses.has(item.status)
})))

const completedCount = computed(() => normalizedData.value.filter(item => item.onTime).length)
const lateCount = computed(() => normalizedData.value.filter(item => item.late).length)
const resolvedCount = computed(() => completedCount.value + lateCount.value)
const completionRate = computed(() => resolvedCount.value
  ? Math.round((completedCount.value / resolvedCount.value) * 100)
  : 0)

const aggregatedData = computed(() => {
  const grouped = {}
  normalizedData.value.forEach(item => {
    const key = item[activeFilters.groupBy]
    if (!grouped[key]) grouped[key] = { name: key, total: 0, onTime: 0, late: 0 }
    grouped[key].total++
    if (item.onTime) grouped[key].onTime++
    if (item.late) grouped[key].late++
  })
  return Object.values(grouped).sort((a, b) => b.total - a.total)
})

const { page, pageItems: pagedStatistics, totalItems } = usePagination(aggregatedData, [
  () => activeFilters.groupBy, () => activeFilters.dateFrom, () => activeFilters.dateTo
])

const groupLabel = computed(() => {
  const labels = { room: 'Tên phòng', slot: 'Ca học', user: 'Người dùng', statusLabel: 'Trạng thái' }
  return labels[activeFilters.groupBy]
})

const timeline = computed(() => buildStatisticsTimeline(normalizedData.value, {
  from: activeFilters.dateFrom, to: activeFilters.dateTo, granularity: chartGranularity.value
}))
const chartUnitLabel = computed(() => ({ day: 'ngày', week: 'tuần', month: 'tháng' })[timeline.value.granularity])
const maxChartCount = computed(() => {
  const maximum = Math.max(1, ...timeline.value.series.map(item => item.count))
  return Math.max(4, Math.ceil(maximum / 4) * 4)
})
const chartPoints = computed(() => timeline.value.series.map((item, index, items) => ({
  ...item,
  x: items.length === 1 ? 400 : 6 + (index / (items.length - 1)) * 788,
  y: 194 - (item.count / maxChartCount.value) * 184
})))
const lineChartPoints = computed(() => chartPoints.value.length
  ? `M ${chartPoints.value.map(point => `${point.x},${point.y}`).join(' L ')}`
  : '')
const lineChartArea = computed(() => lineChartPoints.value
  ? `${lineChartPoints.value} L ${chartPoints.value.at(-1).x},194 L ${chartPoints.value[0].x},194 Z`
  : '')

const chartLabels = computed(() => timelineTicks(timeline.value.series).map(item => ({
  ...item,
  position: timeline.value.series.length === 1 ? 50 : (6 + item.index / (timeline.value.series.length - 1) * 788) / 8
})))

function getStatusLabel(status) {
  return {
    PENDING: 'Chờ nhận', IN_USE: 'Đang mượn', RETURNING: 'Đang trả',
    COMPLETED: 'Đã trả', CANCELED: 'Đã hủy', EXPIRED: 'Hết hạn',
    OVERDUE: 'Quá hạn', FAULT: 'Có sự cố'
  }[status] || status || 'Không xác định'
}

async function fetchStatistics() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const params = new URLSearchParams()
    if (activeFilters.dateFrom) params.set('fromDate', activeFilters.dateFrom)
    if (activeFilters.dateTo) params.set('toDate', activeFilters.dateTo)
    rawData.value = await api.get(`/admin/history/statistics?${params.toString()}`)
  } catch (error) {
    errorMessage.value = error?.message || 'Không thể tải dữ liệu thống kê.'
  } finally {
    isLoading.value = false
  }
}

function openFilterModal() {
  Object.assign(tempFilters, activeFilters)
  showFilterModal.value = true
}

async function applyFilter() {
  if (isInvalidDateRange.value) {
    errorMessage.value = 'Ngày bắt đầu không được lớn hơn ngày kết thúc.'
    return
  }
  Object.assign(activeFilters, tempFilters)
  showFilterModal.value = false
  await fetchStatistics()
}

onMounted(fetchStatistics)
</script>

<template>
  <AdminLayout>
    <div class="w-full text-ink">
      
      <!-- Modal Bộ lọc -->
      <AppModal v-if="showFilterModal" title="Bộ lọc thống kê" @close="showFilterModal = false">
          <div class="flex flex-col gap-5">
            <label class="grid gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Gom nhóm theo
              <select v-model="tempFilters.groupBy" class="modal-field">
                <option value="room">Theo phòng học</option>
                <option value="slot">Theo ca học</option>
                <option value="user">Theo người dùng</option>
                <option value="statusLabel">Theo trạng thái</option>
              </select>
            </label>
            
            <div class="grid grid-cols-2 gap-4">
              <label class="grid gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Từ ngày
                <input v-model="tempFilters.dateFrom" type="date" class="modal-field" />
              </label>
              <label class="grid gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Đến ngày
                <input v-model="tempFilters.dateTo" type="date" class="modal-field" />
              </label>
            </div>
            <p class="text-xs leading-relaxed text-slate-500">Để trống ngày để áp dụng tất cả các ngày. Nếu chỉ nhập một ngày, dữ liệu được lọc từ hoặc đến ngày đó.</p>
            <p v-if="isInvalidDateRange" class="text-xs font-medium text-red-600">
              Ngày bắt đầu không được lớn hơn ngày kết thúc.
            </p>
          </div>
          <template #footer>
            <button type="button" @click="showFilterModal = false" class="modal-cancel">Hủy</button>
            <button type="button" @click="applyFilter" :disabled="isInvalidDateRange" class="modal-primary">Áp dụng</button>
          </template>
        </AppModal>

      <!-- Header -->
      <div class="sticky top-0 z-40 flex flex-col gap-4 border-b border-slate-200/60 bg-mist/95 px-4 pt-6 pb-4 shadow-sm backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8 xl:px-12">
        <AdminPageTitle eyebrow="Analytics Dashboard" title="Thống kê lượt mượn trả" />
        
        <div class="flex flex-wrap items-center gap-3">
          <p class="text-xs font-medium text-slate-500">
            Đang xem theo: <span class="text-brand font-semibold">{{ groupLabel }}</span>
          </p>
          <button @click="openFilterModal" class="flex h-10 items-center justify-center gap-2 rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-md shadow-brand/20 hover:bg-brand-dark transition shrink-0">
            <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Lọc dữ liệu
          </button>
        </div>
      </div>

      <!-- Nội dung dùng cùng lề và nền với các trang quản trị -->
      <div class="px-4 pt-5 pb-10 sm:px-6 lg:px-8 xl:px-12">
      <div v-if="errorMessage" class="mb-5 flex items-center justify-between gap-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
        <span>{{ errorMessage }}</span>
        <button class="shrink-0 font-bold underline underline-offset-2" @click="fetchStatistics">Thử lại</button>
      </div>

      <div v-if="isLoading" class="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Đang tải thống kê">
        <div v-for="index in 4" :key="index" class="h-28 animate-pulse rounded-2xl border border-blue-100 bg-slate-100"></div>
      </div>

      <!-- Thẻ số liệu -->
      <div v-else class="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm flex flex-col justify-between">
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Tổng lượt mượn</p>
          <p class="text-2xl sm:text-3xl font-bold text-ink mt-3 tracking-tight">{{ normalizedData.length }}</p>
        </div>
        
        <div class="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm flex flex-col justify-between">
          <div>
            <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Đã hoàn tất</p>
            <p class="text-2xl sm:text-3xl font-bold text-emerald-600 mt-3 tracking-tight">{{ completedCount }}</p>
          </div>
        </div>

        <div class="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm flex flex-col justify-between">
          <div>
            <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Cần xử lý</p>
            <p class="text-2xl sm:text-3xl font-bold text-red-600 mt-3 tracking-tight">{{ lateCount }}</p>
          </div>
        </div>

        <div class="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm flex flex-col justify-between">
          <div>
            <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Tỷ lệ hoàn tất</p>
            <p class="text-2xl sm:text-3xl font-bold text-brand mt-3 tracking-tight">
              {{ completionRate }}%
            </p>
          </div>
        </div>
      </div>

      <!-- Biểu đồ tổng quan và chuyển chế độ -->
      <div class="mb-5 grid grid-cols-1 gap-5">
        <div class="min-w-0 rounded-2xl border border-blue-100 bg-white p-4 sm:p-6 shadow-sm">
          <div class="flex flex-wrap items-center justify-between gap-3" :class="activeSection === 'overview' ? 'mb-6' : ''">
            <div class="flex items-center gap-2 rounded-xl bg-blue-50/80 p-1 border border-blue-100" role="tablist" aria-label="Chế độ thống kê">
              <button id="statistics-overview-tab" type="button" role="tab" aria-controls="statistics-overview" :aria-selected="activeSection === 'overview'" @click="activeSection = 'overview'"
                :class="activeSection === 'overview' ? 'bg-brand text-white shadow-sm' : 'text-slate-600 hover:text-brand'" class="min-h-10 rounded-lg px-4 py-1.5 text-xs font-bold transition">Biểu đồ tổng quan</button>
              <button id="statistics-details-tab" type="button" role="tab" aria-controls="statistics-details" :aria-selected="activeSection === 'details'" @click="activeSection = 'details'"
                :class="activeSection === 'details' ? 'bg-brand text-white shadow-sm' : 'text-slate-600 hover:text-brand'" class="min-h-10 rounded-lg px-4 py-1.5 text-xs font-bold transition">Chi tiết</button>
            </div>
            <div v-if="activeSection === 'overview'" class="flex flex-wrap items-center gap-2">
              <select v-model="chartGranularity" aria-label="Đơn vị thời gian biểu đồ" class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm text-slate-600 outline-none focus:ring-2 focus:ring-brand">
                <option value="auto">Tự động</option><option value="day">Theo ngày</option><option value="week">Theo tuần</option><option value="month">Theo tháng</option>
              </select>
              <span class="inline-flex items-center rounded-md bg-blue-50 px-2.5 py-1 text-xs font-bold text-brand border border-blue-100">{{ timeline.series.length }} {{ chartUnitLabel }}</span>
            </div>
          </div>

          <div v-show="activeSection === 'overview'" id="statistics-overview" role="tabpanel" aria-labelledby="statistics-overview-tab">
          <p class="mb-3 text-xs text-slate-500">Số lượt mượn theo {{ chartUnitLabel }} · Di chuột vào điểm để xem số lượt.</p>
          <div class="relative w-full h-64 pl-10 pr-2">
            <div class="absolute inset-y-0 left-0 w-8 flex flex-col justify-between py-2 text-right text-[10px] text-slate-400" aria-hidden="true">
              <span>{{ maxChartCount }}</span><span>{{ maxChartCount * 0.75 }}</span><span>{{ maxChartCount * 0.5 }}</span><span>{{ maxChartCount * 0.25 }}</span><span>0</span>
            </div>
            <div class="absolute inset-y-2 left-10 right-2 flex flex-col justify-between pointer-events-none" aria-hidden="true">
              <div v-for="line in 5" :key="line" class="border-b border-blue-50"></div>
            </div>

            <svg viewBox="0 0 800 200" preserveAspectRatio="none" class="w-full h-full relative z-10" role="img" :aria-label="`Biểu đồ số lượt mượn theo ${chartUnitLabel}`">
              <defs>
                <linearGradient id="systemBrandGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="var(--color-brand, #2563eb)" stop-opacity="0.25" />
                  <stop offset="100%" stop-color="var(--color-brand, #2563eb)" stop-opacity="0.0" />
                </linearGradient>
              </defs>
              <path :d="lineChartArea" fill="url(#systemBrandGradient)" />
              <path :d="lineChartPoints" fill="none" stroke="var(--color-brand, #2563eb)" stroke-width="2.5" stroke-linecap="round" />
              <circle v-for="point in chartPoints" :key="point.date" :cx="point.x" :cy="point.y" :r="chartPoints.length > 40 ? 2 : 4" fill="white" stroke="var(--color-brand, #2563eb)" stroke-width="2" tabindex="0" :aria-label="`${chartUnitLabel} ${point.label}: ${point.count} lượt`">
                <title>{{ chartUnitLabel }} {{ point.label }}: {{ point.count }} lượt</title>
              </circle>
            </svg>
            <div v-if="!isLoading && normalizedData.length === 0" class="absolute inset-0 z-20 flex items-center justify-center text-sm font-medium text-slate-400">Không có dữ liệu để vẽ biểu đồ.</div>
          </div>

          <div class="pl-10 pr-2 mt-3">
            <div class="relative h-5 text-[10px] text-slate-500">
              <span v-for="(tick, index) in chartLabels" :key="tick.date" class="absolute whitespace-nowrap"
                :style="{ left: `${tick.position}%`, transform: index === 0 && chartLabels.length > 1 ? 'none' : index === chartLabels.length - 1 && chartLabels.length > 1 ? 'translateX(-100%)' : 'translateX(-50%)' }">{{ tick.label }}</span>
            </div>
          </div>
          </div>
        </div>
      </div>

      <!-- Detail table -->
      <div v-show="activeSection === 'details'" id="statistics-details" role="tabpanel" aria-labelledby="statistics-details-tab" class="rounded-2xl border border-blue-100 bg-white shadow-sm overflow-hidden">
        <div class="px-5 py-4 border-b border-blue-50 bg-blue-50/30">
          <h2 class="text-xs font-bold uppercase tracking-wider text-ink">Bảng chi tiết</h2>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-blue-50 bg-blue-50/60">
                <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500">{{ groupLabel }}</th>
                <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Tổng mượn</th>
                <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Đã hoàn tất</th>
                <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Cần xử lý</th>
                <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500">Tỷ lệ hoàn thành</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-blue-50">
              <tr v-for="item in pagedStatistics" :key="item.name" class="transition hover:bg-blue-50/30">
                <td class="px-5 py-4 font-semibold text-ink">{{ item.name }}</td>
                <td class="px-5 py-4 font-bold text-brand">{{ item.total }}</td>
                <td class="px-5 py-4 font-medium text-emerald-600">{{ item.onTime }}</td>
                <td class="px-5 py-4 font-medium text-red-500">{{ item.late }}</td>
                <td class="px-5 py-4 font-bold text-slate-700">
                  {{ Math.round((item.onTime / item.total) * 100) }}%
                </td>
              </tr>
              <tr v-if="!isLoading && aggregatedData.length === 0">
                <td colspan="5" class="py-16 text-center text-slate-400 font-medium text-xs">Không có dữ liệu trong khoảng thời gian này.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <TablePagination v-model:page="page" :total-items="totalItems" :disabled="isLoading" label="nhóm thống kê" />
      </div>
      </div>
    </div>
  </AdminLayout>
</template>
