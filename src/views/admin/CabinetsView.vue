<script setup>
import AppModal from '@/components/shared/AppModal.vue'
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import AdminPageTitle from '@/components/admin/layout/AdminPageTitle.vue'
import TablePagination from '@/components/shared/TablePagination.vue'
import { usePagination } from '@/composables/usePagination.js'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api } from '@/services/apiClient.js'
import { cabinetHub } from '@/services/cabinetHub.js'

const search = ref('')
const statusFilter = ref('Trạng thái tủ')
const doorFilter = ref('Tình trạng cửa')
const networkFilter = ref('Kết nối')
const isLoading = ref(false)
const cabinets = ref([])

let unsubscribeCabinetStatus = null

// HÀM NÀY CHỈ CHẠY 1 LẦN DUY NHẤT KHI VÀO TRANG HOẶC BẤM NÚT LÀM MỚI THỦ CÔNG
async function fetchCabinets() {
  isLoading.value = true

  try {
    cabinets.value = await api.get('/admin/cabinets')
  } catch (err) {
    console.error('Lỗi tải danh sách tủ:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(async () => {
  // 1. Chỉ gọi HTTP GET đúng 1 lần khi load trang
  await fetchCabinets()

  // 2. Khởi tạo SignalR
  // 3. LẮNG NGHE VÀ CẬP NHẬT VI PHÂN (DELTA UPDATE) - KHÔNG GỌI LẠI HTTP GET
  unsubscribeCabinetStatus = cabinetHub.subscribe('CabinetStatusChanged', (data) => {
    const target = cabinets.value.find(c =>
      String(c.roomId || '').toLowerCase() === String(data.roomId || '').toLowerCase() ||
      String(c.id) === String(data.roomId)
    )

    if (target) {
      // Cập nhật trực tiếp trên RAM, Vue tự động re-render UI tức thì (0% tốn băng thông)
      target.doorCondition = data.doorCondition || (data.isOpen ? 'Mở' : 'Đóng')
      target.isDoorOpen = data.isOpen
      target.isOnline = data.isOnline ?? true

      if (data.status) target.status = data.status
      if (data.borrower !== undefined) target.borrower = data.borrower
      if (data.lastOnline) target.lastOnline = data.lastOnline
    }
  })

  try {
    await cabinetHub.start()
    console.log('[Cabinets] Da ket noi Realtime Hub!')
  } catch (err) {
    console.error('[Cabinets] Loi ket noi SignalR:', err)
  }
})

onUnmounted(() => {
  if (unsubscribeCabinetStatus) unsubscribeCabinetStatus()
})

const confirmModal = ref({
  show: false,
  title: '',
  message: '',
  cabName: '',
  actionLabel: 'Xác nhận',
  confirmVariant: 'primary',
  isProcessing: false,
  onConfirm: null
})

const toast = ref({
  show: false,
  message: '',
  type: 'success',
  timer: null
})

function showToastMessage(message, type = 'success') {
  if (toast.value.timer) clearTimeout(toast.value.timer)
  toast.value = {
    show: true,
    message,
    type,
    timer: setTimeout(() => {
      toast.value.show = false
    }, 3500)
  }
}

function closeConfirmModal() {
  if (confirmModal.value.isProcessing) return
  confirmModal.value.show = false
}

async function executeModalAction() {
  if (!confirmModal.value.onConfirm) return
  confirmModal.value.isProcessing = true
  try {
    await confirmModal.value.onConfirm()
    confirmModal.value.show = false
  } catch (err) {
    showToastMessage(err.message || 'Thao tác không thành công!', 'error')
  } finally {
    confirmModal.value.isProcessing = false
  }
}

// Mở khóa khẩn cấp từ xa
function handleRemoteOpen(cab) {
  if (!cab.isOnline) {
    showToastMessage('Tủ đang OFFLINE, không thể mở từ xa!', 'warning')
    return
  }
  if (cab.status === 'Bảo trì') {
    showToastMessage('Tủ đang ở chế độ BẢO TRÌ, không thể mở!', 'warning')
    return
  }

  confirmModal.value = {
    show: true,
    title: 'Mở khóa tủ khẩn cấp',
    message: 'Lệnh này sẽ gửi tín hiệu mở chốt điện khẩn cấp đến thiết bị phần cứng ngay lập tức.',
    cabName: cab.name,
    actionLabel: 'Mở khóa ngay',
    confirmVariant: 'primary',
    isProcessing: false,
    onConfirm: async () => {
      await api.post(`/admin/cabinets/remote-open/${cab.id}`)
      cab.doorCondition = 'Mở'
      cab.isDoorOpen = true
      showToastMessage(`Đã gửi lệnh mở khóa cho ${cab.name} thành công!`, 'success')
    }
  }
}

// Khóa tủ từ xa
function handleRemoteLock(cab) {
  confirmModal.value = {
    show: true,
    title: 'Khóa chốt tủ từ xa',
    message: 'Lệnh này sẽ gửi tín hiệu kích hoạt chốt khóa điện tử của tủ đồ.',
    cabName: cab.name,
    actionLabel: 'Khóa tủ',
    confirmVariant: 'warning',
    isProcessing: false,
    onConfirm: async () => {
      await api.post(`/admin/cabinets/remote-lock/${cab.id}`)
      cab.doorCondition = 'Đóng'
      cab.isDoorOpen = false
      showToastMessage(`Đã gửi lệnh khóa chốt cho ${cab.name}!`, 'success')
    }
  }
}

// Đổi trạng thái Bảo trì / Khôi phục
function handleToggleMaintenance(cab) {
  const isMaintenance = cab.status === 'Bảo trì'
  const actionText = isMaintenance ? 'Khôi phục hoạt động' : 'Chuyển sang chế độ bảo trì'

  confirmModal.value = {
    show: true,
    title: actionText,
    message: isMaintenance
      ? `Khôi phục ${cab.name} trở lại trạng thái sẵn sàng để người dùng có thể mượn thiết bị.`
      : `Đưa ${cab.name} vào chế độ bảo trì. Sinh viên/giảng viên sẽ không thể đăng ký mượn tủ này.`,
    cabName: cab.name,
    actionLabel: isMaintenance ? 'Khôi phục' : 'Bật bảo trì',
    confirmVariant: isMaintenance ? 'primary' : 'danger',
    isProcessing: false,
    onConfirm: async () => {
      const data = await api.patch(`/admin/cabinets/${cab.id}/toggle-maintenance`)
      cab.status = data?.status || (isMaintenance ? 'Trống' : 'Bảo trì')
      showToastMessage(`Đã cập nhật trạng thái của ${cab.name} thành công!`, 'success')
    }
  }
}

const filteredCabinets = computed(() => {
  return cabinets.value.filter(c => {
    const matchStatus = statusFilter.value === 'Trạng thái tủ' || c.status === statusFilter.value
    const matchDoor = doorFilter.value === 'Tình trạng cửa' || c.doorCondition === doorFilter.value
    const matchNetwork = networkFilter.value === 'Kết nối'
      || (networkFilter.value === 'Online' && c.isOnline)
      || (networkFilter.value === 'Offline' && !c.isOnline)

    const keyword = search.value.toLowerCase().trim()
    const matchSearch = !keyword
      || (c.name && c.name.toLowerCase().includes(keyword))
      || (c.building && c.building.toLowerCase().includes(keyword))
      || (c.floor && c.floor.toLowerCase().includes(keyword))
      || (c.borrower && c.borrower.toLowerCase().includes(keyword))
      || (c.roomId && c.roomId.toLowerCase().includes(keyword))

    return matchStatus && matchDoor && matchNetwork && matchSearch
  })
})
const { page, pageItems: pagedCabinets, totalItems } = usePagination(filteredCabinets, [search, statusFilter, doorFilter, networkFilter])
</script>

<template>
  <AdminLayout>
    <div class="w-full">
      <!-- Header NEO CỐ ĐỊNH -->
      <div
        class="sticky top-0 z-40 bg-mist/95 backdrop-blur-sm border-b border-slate-200/60 shadow-sm px-4 sm:px-6 lg:px-8 xl:px-12 pt-6 pb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <AdminPageTitle eyebrow="Quản lý phần cứng" title="Tủ đồ thiết bị thông minh" />
        <div class="flex items-center gap-3">
          <button @click="fetchCabinets" :disabled="isLoading"
            class="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 h-10 text-xs font-bold text-slate-600 hover:bg-slate-50 transition shadow-sm disabled:opacity-60">
            <font-awesome-icon icon="fa-solid fa-arrows-rotate" :class="{ 'animate-spin': isLoading }"
              class="size-3.5 text-slate-500 mr-1" />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      <!-- Nội dung Body -->
      <div class="px-4 sm:px-6 lg:px-8 xl:px-12 pt-5 pb-10">

        <!-- Filter bar -->
        <div class="mb-5 flex flex-col sm:flex-row gap-3">
          <input v-model="search" type="text" placeholder="Tìm theo tên tủ, phòng, tòa nhà, người mượn..."
            class="h-11 flex-1 rounded-xl border border-blue-100 bg-white px-4 text-sm outline-none focus:ring-2 focus:ring-blue-500 shadow-sm" />

          <select v-model="statusFilter"
            class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 sm:w-44 shadow-sm">
            <option>Trạng thái tủ</option>
            <option>Trống</option>
            <option>Đang mượn</option>
            <option>Bảo trì</option>
          </select>

          <select v-model="networkFilter"
            class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 sm:w-44 shadow-sm">
            <option>Kết nối</option>
            <option>Online</option>
            <option>Offline</option>
          </select>

          <select v-model="doorFilter"
            class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 sm:w-44 shadow-sm">
            <option>Tình trạng cửa</option>
            <option>Đóng</option>
            <option>Mở</option>
          </select>
        </div>

        <!-- Table Danh sách Tủ -->
        <div class="rounded-2xl border border-blue-100 bg-white shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-blue-50 bg-blue-50/60">
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Tên tủ / Phòng</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Vị trí</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Kết nối</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Trạng thái</th>
                  <th
                    class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Tình trạng cửa</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Người đang mượn</th>
                  <th
                    class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Thao tác</th>
                </tr>
              </thead>
              <tbody>
                <!-- Skeleton Loading Rows khi đang tải dữ liệu -->
                <template v-if="isLoading">
                  <tr v-for="i in 5" :key="`skel-${i}`" class="border-b border-blue-50/60 animate-pulse">
                    <td class="px-5 py-4">
                      <div class="h-4 w-28 bg-slate-200 rounded"></div>
                      <div class="h-2.5 w-20 bg-slate-100 rounded mt-2"></div>
                    </td>
                    <td class="px-5 py-4">
                      <div class="h-4 w-24 bg-slate-200 rounded"></div>
                    </td>
                    <td class="px-5 py-4">
                      <div class="h-5 w-14 bg-slate-200 rounded-md"></div>
                    </td>
                    <td class="px-5 py-4">
                      <div class="h-5 w-16 bg-slate-200 rounded-md"></div>
                    </td>
                    <td class="px-5 py-4 text-center">
                      <div class="h-5 w-12 bg-slate-200 rounded-lg mx-auto"></div>
                    </td>
                    <td class="px-5 py-4">
                      <div class="h-4 w-20 bg-slate-100 rounded"></div>
                    </td>
                    <td class="px-5 py-4 text-center">
                      <div class="h-7 w-28 bg-slate-200 rounded-lg mx-auto"></div>
                    </td>
                  </tr>
                </template>

                <!-- Danh sách dữ liệu thực tế -->
                <template v-else-if="filteredCabinets.length > 0">
                  <tr v-for="cab in pagedCabinets" :key="cab.id"
                    class="border-b border-blue-50 transition hover:bg-blue-50/30">

                    <td class="px-5 py-4 font-bold text-slate-800 whitespace-nowrap">
                      <div class="flex items-center gap-2">
                        <span class="size-2 rounded-full"
                          :class="cab.isOnline ? 'bg-emerald-500' : 'bg-slate-300'"></span>
                        <div>
                          <p class="font-bold text-slate-900">{{ cab.name }}</p>
                          <p class="text-[11px] text-slate-400 font-normal">Topic: {{ cab.mqttTopic }}</p>
                        </div>
                      </div>
                    </td>

                    <td class="px-5 py-4 font-medium text-slate-600 whitespace-nowrap">
                      <span class="font-semibold text-slate-800">{{ cab.building }}</span> • {{ cab.floor }}
                    </td>

                    <td class="px-5 py-4 whitespace-nowrap">
                      <span
                        :class="cab.isOnline ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'"
                        class="rounded-md border px-2 py-0.5 text-[12px] font-bold">
                        {{ cab.isOnline ? 'Online' : 'Offline' }}
                      </span>
                    </td>

                    <!-- Trạng thái mượn -->
                    <td class="px-5 py-4 whitespace-nowrap">
                      <span :class="{
                        'bg-emerald-100 text-emerald-700': cab.status === 'Trống',
                        'bg-amber-100 text-amber-700': cab.status === 'Đang mượn',
                        'bg-red-100 text-red-700': cab.status === 'Bảo trì'
                      }" class="rounded-md px-2.5 py-1 text-xs font-bold">
                        {{ cab.status }}
                      </span>
                    </td>

                    <!-- Tình trạng cửa tủ: MỞ = VÀNG CAM CẢNH BÁO, ĐÓNG = XANH LÁ AN TOÀN -->
                    <td class="px-5 py-4 text-center whitespace-nowrap">
                      <span :class="cab.doorCondition === 'Mở'
                        ? 'bg-amber-100 text-amber-800 border border-amber-300 shadow-sm animate-pulse'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
                        class="inline-flex items-center justify-center gap-1 rounded-lg px-3 py-1 text-xs font-bold">
                        <span>{{ cab.doorCondition === 'Mở' ? 'Mở' : 'Đóng' }}</span>
                      </span>
                    </td>

                    <!-- Người mượn -->
                    <td class="px-5 py-4 font-medium text-slate-600 whitespace-nowrap">
                      <span :class="cab.borrower !== '---' ? 'text-blue-600 font-semibold' : 'text-slate-400'">
                        {{ cab.borrower }}
                      </span>
                    </td>

                    <!-- Thao tác Admin -->
                    <td class="px-5 py-4 text-center whitespace-nowrap">
                      <div class="flex items-center justify-center gap-2">
                        <!-- Nút Mở / Khóa cửa tủ -->
                        <button v-if="cab.doorCondition === 'Đóng'" @click="handleRemoteOpen(cab)"
                          class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200"
                          title="Mở tủ khẩn cấp từ xa">
                          Mở tủ
                        </button>
                        <button v-else @click="handleRemoteLock(cab)"
                          class="rounded-lg bg-amber-50 px-2.5 py-1 text-xs font-bold text-amber-700 hover:bg-amber-600 hover:text-white active:scale-95 transition border border-amber-200"
                          title="Khóa chốt tủ">
                          Khóa tủ
                        </button>

                        <!-- Nút Chuyển chế độ Bảo trì -->
                        <button @click="handleToggleMaintenance(cab)"
                          :class="cab.status === 'Bảo trì' ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-600 hover:text-white' : 'bg-red-50 text-red-600 border-red-200 hover:bg-red-600 hover:text-white'"
                          class="rounded-lg px-2.5 py-1 text-xs font-bold active:scale-95 transition border">
                          {{ cab.status === 'Bảo trì' ? 'Khôi phục' : 'Bảo trì' }}
                        </button>
                      </div>
                    </td>

                  </tr>
                </template>

                <!-- Trạng thái trống không có dữ liệu -->
                <tr v-else>
                  <td colspan="7" class="py-16 text-center text-slate-400">
                    <svg class="size-9 mx-auto text-slate-300 mb-2" fill="none" viewBox="0 0 24 24"
                      stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <p class="text-sm font-medium">Không tìm thấy tủ đồ nào phù hợp bộ lọc.</p>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <TablePagination v-model:page="page" :total-items="totalItems" :disabled="isLoading" label="tủ thiết bị" />
        </div>

      </div>
    </div>

    <!-- Custom Confirmation Dialog (Replaces native browser confirm) -->
    <AppModal v-if="confirmModal.show" :title="confirmModal.title" size="md" :busy="confirmModal.isProcessing"
      @close="closeConfirmModal">
      <p class="text-sm leading-relaxed text-slate-500">{{ confirmModal.message }}</p>
      <div
        class="mt-4 flex items-center justify-between gap-3 rounded-xl border border-blue-100 bg-blue-50/40 p-3 text-sm">
        <span class="text-slate-500">Tủ tác động</span><span class="font-semibold text-ink">{{ confirmModal.cabName
          }}</span>
      </div>
      <template #footer>
        <button type="button" @click="closeConfirmModal" :disabled="confirmModal.isProcessing"
          class="modal-cancel">Hủy</button>
        <button @click="executeModalAction" :disabled="confirmModal.isProcessing"
          :class="{ 'modal-warning': confirmModal.confirmVariant === 'warning', 'modal-danger': confirmModal.confirmVariant === 'danger' }"
          class="modal-primary">
          <svg v-if="confirmModal.isProcessing" class="size-3.5 animate-spin text-white" fill="none"
            viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z">
            </path>
          </svg>
          <span>{{ confirmModal.isProcessing ? 'Đang gửi lệnh...' : confirmModal.actionLabel }}</span>
        </button>
      </template>
    </AppModal>

    <!-- Toast Notification (Replaces native browser alert) -->
    <div v-if="toast.show" :class="{
      'bg-emerald-600 text-white border-emerald-500 shadow-emerald-900/20': toast.type === 'success',
      'bg-rose-600 text-white border-rose-500 shadow-rose-900/20': toast.type === 'error',
      'bg-amber-500 text-white border-amber-400 shadow-amber-900/20': toast.type === 'warning'
    }"
      class="fixed bottom-6 right-6 z-[60] flex items-center gap-3 rounded-2xl border px-4 py-3 text-xs font-semibold shadow-xl transition-all">
      <svg v-if="toast.type === 'success'" class="size-4 shrink-0 text-white" fill="none" viewBox="0 0 24 24"
        stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
      </svg>
      <svg v-else-if="toast.type === 'warning'" class="size-4 shrink-0 text-white" fill="none" viewBox="0 0 24 24"
        stroke="currentColor" stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <svg v-else class="size-4 shrink-0 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"
        stroke-width="2.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
      <span>{{ toast.message }}</span>
    </div>
  </AdminLayout>
</template>
