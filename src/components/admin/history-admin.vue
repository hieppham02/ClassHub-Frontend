<script setup>
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '@/services/apiClient.js'

const search = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const statusFilter = ref('Tất cả')
const isLoading = ref(false)
const historyList = ref([])

// 1. Tải danh sách lịch sử từ API
async function fetchHistory() {
  isLoading.value = true

  const params = new URLSearchParams()
  if (search.value.trim()) params.append('search', search.value.trim())
  if (statusFilter.value !== 'Tất cả') params.append('status', statusFilter.value)
  if (dateFrom.value) params.append('fromDate', dateFrom.value)
  if (dateTo.value) params.append('toDate', dateTo.value)

  try {
    historyList.value = await api.get(`/admin/history?${params.toString()}`)
  } catch (err) {
    console.error('Lỗi khi tải lịch sử:', err)
  } finally {
    isLoading.value = false
  }
}

// Theo dõi thay đổi của bộ lọc
watch([statusFilter, dateFrom, dateTo], () => {
  fetchHistory()
})

onMounted(() => {
  fetchHistory()
})

// Xử lý tìm kiếm khi người dùng nhấn Enter hoặc bấm icon
function handleSearch() {
  fetchHistory()
}

// 2. Xuất file CSV chuẩn UTF-8
function exportCSV() {
  if (historyList.value.length === 0) return alert('Không có dữ liệu để xuất!')

  const headers = ['Mã Đơn', 'Tên phòng', 'Ca học', 'Ngày mượn', 'Người mượn', 'Mã SV mượn', 'SĐT mượn', 'Mượn lúc', 'Người trả', 'SĐT trả', 'Trả lúc', 'Trạng thái', 'Ghi chú']
  
  const rows = historyList.value.map(row => [
    row.id,
    row.room,
    row.slot,
    row.displayDate,
    row.borrower,
    row.borrowerId,
    row.phoneBorrow,
    row.timeBorrow,
    row.returner,
    row.phoneReturn,
    row.timeReturn,
    row.status,
    row.returnNote || ''
  ])

  const csvContent = [headers.join(','), ...rows.map(r => r.map(field => `"${field}"`).join(','))].join('\n')
  
  // Thêm '\uFEFF' để Excel mở file Tiếng Việt không bị lỗi font
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const fileUrl = URL.createObjectURL(blob)
  link.setAttribute('href', fileUrl)
  link.setAttribute('download', `LichSuMuonTra_${new Date().toISOString().slice(0, 10)}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<template>
  <AdminLayout>
    <div class="w-full">
      <!-- Header NEO CỐ ĐỊNH -->
      <div class="sticky top-0 z-40 bg-mist/95 backdrop-blur-sm border-b border-slate-200/60 shadow-sm px-4 sm:px-6 lg:px-32 pt-6 pb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-widest text-slate-400">Kiểm toán &amp; Thống kê</p>
          <h1 class="mt-0.5 text-2xl font-black text-ink">Lịch sử mượn trả thiết bị</h1>
        </div>
        <div class="flex items-center gap-3">
          <button 
            @click="fetchHistory" 
            :disabled="isLoading"
            class="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 h-10 text-xs font-bold text-slate-600 hover:bg-slate-50 transition shadow-sm"
          >
            <span :class="{ 'animate-spin': isLoading }"><font-awesome-icon icon="fa-solid fa-arrows-rotate" class="size-4 text-slate-500" /> </span>
            <span>Làm mới</span>
          </button>
          <button 
            @click="exportCSV" 
            class="h-10 rounded-xl border border-brand px-5 text-sm font-bold text-brand hover:bg-blue-50 transition shrink-0 bg-white shadow-sm"
          >
            ↓ Xuất CSV
          </button>
        </div>
      </div>

      <!-- Nội dung Body -->
      <div class="px-4 sm:px-6 lg:px-32 pt-5 pb-10">
        
        <!-- Filter bar -->
        <div class="mb-5 flex flex-col xl:flex-row items-end gap-3">
          <div class="relative w-full xl:flex-1">
            <input 
              v-model="search" 
              @keyup.enter="handleSearch"
              type="text" 
              placeholder="Tìm tên phòng, mã SV, người mượn, người trả, SĐT..." 
              class="h-11 w-full rounded-xl border border-blue-100 bg-white px-4 pr-10 text-sm outline-none focus:ring-2 focus:ring-brand shadow-sm" 
            />
            <button 
              v-if="search" 
              @click="search = ''; fetchHistory()" 
              class="absolute right-3 top-1/2 -translate-y-1/2 flex size-6 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
            >
              <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          <div class="flex flex-col sm:flex-row w-full xl:w-auto gap-3">
            <label class="w-full sm:w-auto grid gap-1 text-xs font-semibold text-slate-500 shrink-0">
              Trạng thái
              <select v-model="statusFilter" class="h-11 w-full sm:w-36 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-brand shadow-sm">
                <option>Tất cả</option>
                <option value="COMPLETED">Đã hoàn thành</option>
                <option value="IN_USE">Đang mượn (IN_USE)</option>
                <option value="PENDING">Chờ lấy đồ (PENDING)</option>
                <option value="OVERDUE">Quá hạn (OVERDUE)</option>
                <option value="CANCELED">Đã hủy</option>
              </select>
            </label>

            <label class="w-full sm:w-auto grid gap-1 text-xs font-semibold text-slate-500 shrink-0">
              Từ ngày
              <input v-model="dateFrom" type="date" class="h-11 w-full sm:w-36 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-brand shadow-sm" />
            </label>

            <label class="w-full sm:w-auto grid gap-1 text-xs font-semibold text-slate-500 shrink-0">
              Đến ngày
              <input v-model="dateTo" type="date" class="h-11 w-full sm:w-36 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-brand shadow-sm" />
            </label>
          </div>
        </div>

        <!-- Table -->
        <div class="rounded-2xl border border-blue-100 bg-white shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-blue-50 bg-blue-50/60">
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Tên phòng</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Ca học</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Ngày mượn</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Người mượn</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">SĐT mượn</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Mượn lúc</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Người trả</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">SĐT trả</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Trả lúc</th>
                  <th class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in historyList" :key="record.id" class="border-b border-blue-50 transition hover:bg-blue-50/30">
                  <td class="px-5 py-3.5 font-bold text-slate-900 whitespace-nowrap">{{ record.room }}</td>
                  <td class="px-5 py-3.5 text-slate-600 whitespace-nowrap">{{ record.slot }}</td>
                  <td class="px-5 py-3.5 text-slate-600 whitespace-nowrap">{{ record.displayDate }}</td>
                  
                  <!-- Người mượn -->
                  <td class="px-5 py-3.5 whitespace-nowrap">
                    <p class="font-medium text-ink">{{ record.borrower }}</p>
                    <p class="text-[11px] text-slate-400 font-normal">Mã: {{ record.borrowerId }}</p>
                  </td>
                  
                  <td class="px-5 py-3.5 text-slate-600 whitespace-nowrap">{{ record.phoneBorrow }}</td>
                  <td class="px-5 py-3.5 font-semibold text-slate-700 whitespace-nowrap">{{ record.timeBorrow }}</td>
                  
                  <!-- Người trả -->
                  <td class="px-5 py-3.5 whitespace-nowrap">
                    <span :class="record.returner !== '---' ? 'text-slate-800 font-medium' : 'text-slate-400'">
                      {{ record.returner }}
                    </span>
                    <span v-if="record.delegateTo" class="block text-[10px] text-blue-600 font-semibold">(Ủy quyền)</span>
                  </td>
                  
                  <td class="px-5 py-3.5 text-slate-600 whitespace-nowrap">{{ record.phoneReturn }}</td>
                  <td class="px-5 py-3.5 font-semibold text-slate-700 whitespace-nowrap">{{ record.timeReturn }}</td>
                  
                  <!-- Trạng thái -->
                  <td class="px-5 py-3.5 text-center whitespace-nowrap">
                    <span 
                      :class="{
                        'bg-emerald-100 text-emerald-700': record.status === 'COMPLETED', 
                        'bg-amber-100 text-amber-700': record.status === 'IN_USE' || record.status === 'ACTIVE', 
                        'bg-blue-100 text-blue-700': record.status === 'PENDING',
                        'bg-red-100 text-red-700': record.status === 'OVERDUE' || record.status === 'CANCELED'
                      }" 
                      class="rounded-md px-2.5 py-1 text-xs font-bold"
                    >
                      {{ record.status }}
                    </span>
                  </td>
                </tr>

                <tr v-if="historyList.length === 0">
                  <td colspan="10" class="py-16 text-center text-slate-400">
                    {{ isLoading ? 'Đang tải dữ liệu lịch sử...' : 'Không tìm thấy lượt mượn nào phù hợp.' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  </AdminLayout>
</template>
