<script setup>
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { api } from '@/services/apiClient.js'
import { cabinetHub } from '@/services/cabinetHub.js'

const search = ref('')
const statusFilter = ref('Trạng thái tủ')
const doorFilter = ref('Tình trạng cửa')
const networkFilter = ref('Tình trạng mạng')
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

// Mở khóa khẩn cấp từ xa
async function handleRemoteOpen(cab) {
  if(!cab.isOnline) {
    alert('Tủ đang OFFLINE, không thể mở!')
    return
  }
  if (cab.status === 'Bảo trì') {
    alert('Tủ đang ở chế độ BẢO TRÌ, không thể mở!')
    return
  }
  if (!confirm(`Bạn có chắc chắn muốn gửi lệnh MỞ KHÓA cho ${cab.name}?`)) return

  try {
    await api.post(`/admin/cabinets/remote-open/${cab.id}`)
    cab.doorCondition = 'Mở'
    cab.isDoorOpen = true
  } catch (err) {
    alert(err.message || 'Lỗi kết nối máy chủ!')
  }
}

// Khóa tủ từ xa
async function handleRemoteLock(cab) {
  try {
    await api.post(`/admin/cabinets/remote-lock/${cab.id}`)
    cab.doorCondition = 'Đóng'
    cab.isDoorOpen = false
  } catch (err) {
    console.error(err)
  }
}

// Đổi trạng thái Bảo trì / Khôi phục
async function handleToggleMaintenance(cab) {
  const actionText = cab.status === 'Bảo trì' ? 'KHÔI PHỤC HOẠT ĐỘNG' : 'CHUYỂN SANG BẢO TRÌ'
  if (!confirm(`Bạn có chắc muốn ${actionText} cho ${cab.name}?`)) return

  try {
    const data = await api.patch(`/admin/cabinets/${cab.id}/toggle-maintenance`)
    cab.status = data?.status || (cab.status === 'Bảo trì' ? 'Trống' : 'Bảo trì')
  } catch (err) {
    alert(err.message || 'Lỗi kết nối máy chủ!')
  }
}

const filteredCabinets = computed(() => {
  return cabinets.value.filter(c => {
    const matchStatus = statusFilter.value === 'Trạng thái tủ' || c.status === statusFilter.value
    const matchDoor = doorFilter.value === 'Tình trạng cửa' || c.doorCondition === doorFilter.value
    const matchNetwork = networkFilter.value === 'Tình trạng mạng'
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
</script>

<template>
  <AdminLayout>
    <div class="w-full">
      <!-- Header NEO CỐ ĐỊNH -->
      <div class="sticky top-0 z-40 bg-mist/95 backdrop-blur-sm border-b border-slate-200/60 shadow-sm px-4 sm:px-6 lg:px-32 pt-6 pb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-widest text-slate-400">Quản lý phần cứng</p>
          <h1 class="mt-0.5 text-2xl font-black text-slate-800">Tủ đồ thiết bị thông minh</h1>
        </div>
        <div class="flex items-center gap-3">
          <button 
            @click="fetchCabinets" 
            :disabled="isLoading"
            class="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 h-10 text-xs font-bold text-slate-600 hover:bg-slate-50 transition shadow-sm disabled:opacity-60"
          >
            <font-awesome-icon 
              icon="fa-solid fa-arrows-rotate" 
              :class="{ 'animate-spin': isLoading }"
              class="size-3.5 text-slate-500 mr-1" 
            />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      <!-- Nội dung Body -->
      <div class="px-4 sm:px-6 lg:px-32 pt-5 pb-10">

        <!-- Filter bar -->
        <div class="mb-5 flex flex-col sm:flex-row gap-3">
          <input 
            v-model="search" 
            type="text" 
            placeholder="Tìm theo tên tủ, phòng, tòa nhà, người mượn..." 
            class="h-11 flex-1 rounded-xl border border-blue-100 bg-white px-4 text-sm outline-none focus:ring-2 focus:ring-blue-500 shadow-sm" 
          />

          <select v-model="statusFilter" class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 sm:w-44 shadow-sm">
            <option>Trạng thái tủ</option>
            <option>Trống</option>
            <option>Đang mượn</option>
            <option>Bảo trì</option>
          </select>

          <select v-model="networkFilter" class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 sm:w-44 shadow-sm">
            <option>Tình trạng mạng</option>
            <option>Online</option>
            <option>Offline</option>
          </select>

          <select v-model="doorFilter" class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500 sm:w-44 shadow-sm">
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
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Tên tủ / Phòng</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Vị trí</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Mạng</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Trạng thái</th>
                  <th class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Tình trạng cửa</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Người đang mượn</th>
                  <th class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="cab in filteredCabinets" :key="cab.id" class="border-b border-blue-50 transition hover:bg-blue-50/30">

                  <td class="px-5 py-4 font-bold text-slate-800 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <span class="size-2 rounded-full" :class="cab.isOnline ? 'bg-emerald-500' : 'bg-slate-300'"></span>
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
                      class="rounded-md border px-2 py-0.5 text-[12px] font-bold"
                    >
                      {{ cab.isOnline ? 'Online' : 'Offline' }}
                    </span>
                  </td>

                  <!-- Trạng thái mượn -->
                  <td class="px-5 py-4 whitespace-nowrap">
                    <span 
                      :class="{
                        'bg-emerald-100 text-emerald-700': cab.status === 'Trống',
                        'bg-amber-100 text-amber-700': cab.status === 'Đang mượn',
                        'bg-red-100 text-red-700': cab.status === 'Bảo trì'
                      }" 
                      class="rounded-md px-2.5 py-1 text-xs font-bold"
                    >
                      {{ cab.status }}
                    </span>
                  </td>

                  <!-- Tình trạng cửa tủ: MỞ = VÀNG CAM CẢNH BÁO, ĐÓNG = XANH LÁ AN TOÀN -->
                  <td class="px-5 py-4 text-center whitespace-nowrap">
                    <span 
                      :class="cab.doorCondition === 'Mở'
                        ? 'bg-amber-100 text-amber-800 border border-amber-300 shadow-sm animate-pulse'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
                      class="inline-flex items-center justify-center gap-1 rounded-lg px-3 py-1 text-xs font-bold"
                    >
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
                      <button 
                        v-if="cab.doorCondition === 'Đóng'" 
                        @click="handleRemoteOpen(cab)"
                        class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white transition border border-blue-200"
                        title="Mở tủ khẩn cấp từ xa"
                      >
                        Mở tủ
                      </button>
                      <button 
                        v-else 
                        @click="handleRemoteLock(cab)"
                        class="rounded-lg bg-amber-50 px-2.5 py-1 text-xs font-bold text-amber-700 hover:bg-amber-600 hover:text-white transition border border-amber-200"
                        title="Khóa chốt tủ"
                      >
                        Khóa tủ
                      </button>

                      <!-- Nút Chuyển chế độ Bảo trì -->
                      <button 
                        @click="handleToggleMaintenance(cab)"
                        :class="cab.status === 'Bảo trì' ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-600 hover:text-white' : 'bg-red-50 text-red-600 border-red-200 hover:bg-red-600 hover:text-white'"
                        class="rounded-lg px-2.5 py-1 text-xs font-bold transition border"
                      >
                        {{ cab.status === 'Bảo trì' ? 'Khôi phục' : 'Bảo trì' }}
                      </button>
                    </div>
                  </td>

                </tr>

                <tr v-if="filteredCabinets.length === 0">
                  <td colspan="7" class="py-16 text-center text-slate-400">
                    {{ isLoading ? 'Đang tải dữ liệu từ hệ thống...' : 'Không tìm thấy tủ đồ nào phù hợp.' }}
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
