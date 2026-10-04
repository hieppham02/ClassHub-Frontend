<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import Navbar from '@/components/shared/Navbar.vue'
import BottomNav from '@/components/shared/BottomNav.vue'
import { api } from '@/services/apiClient.js'
import { cabinetHub } from '@/services/cabinetHub.js'

const currentPath = ref(window.location.pathname)
const user = ref({ name: '', role: '' })

const rooms = ref([])
const activeBooking = ref(null)
const booked = ref([])

const date = ref(new Date().toLocaleDateString('en-CA'))
const slot = ref('Chọn ca học')
const danhSachCaHoc = ['Ca 1 (07:00 - 09:30)', 'Ca 2 (09:40 - 12:10)', 'Ca 3 (13:00 - 15:30)', 'Ca 4 (15:40 - 18:10)', 'Ca 5 (18:10 - 20:40)']
const selectedBuilding = ref('Tất cả tòa')
const selectedFloor = ref('Tất cả tầng')

const selectedCabinet = ref(null)
const otpValue = ref('')
const delegateId = ref('')
const confirmReturnId = ref(null)
const showMissingSlotModal = ref(false)
const showToast = ref(false)
const toastMessage = ref('')
const showErrorToast = ref(false)
const errorMessage = ref('')
const previewEquipment = ref(null)

let unsubscribeCabinetStatus = null

function logout() {
  sessionStorage.removeItem('classhub-token')
  sessionStorage.removeItem('classhub-user')
  window.location.href = '/login'
}

function showSuccessToast(msg) { 
  toastMessage.value = msg
  showToast.value = true
  setTimeout(() => showToast.value = false, 3000) 
}

function triggerError(msg) { 
  errorMessage.value = msg
  showErrorToast.value = true
  setTimeout(() => showErrorToast.value = false, 3000) 
}

function onDelegateInput(e) { 
  delegateId.value = e.target.value.replace(/\D/g, '').slice(0, 8) 
}

async function fetchRooms() {
  try {
    const response = await api.get('/rooms/get-rooms')
    if (Array.isArray(response)) {
      rooms.value = response
      rooms.value.forEach(r => {
        if (!r.equipment) {
          r.equipment = [
            { name: 'Máy chiếu', image: 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=300&auto=format&fit=crop&q=60' },
            { name: 'Micro không dây', image: 'https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=300&auto=format&fit=crop&q=60' },
            { name: 'Bút laser', image: '' }
          ]
        }
        if (!r.floor) r.floor = 'Tầng 1'
        if (!r.building) r.building = 'Tòa EAUT'
      })
    }
  } catch (err) { 
    console.error('Lỗi tải phòng:', err) 
  }
}

async function fetchActiveSession() {
  try {
    const response = await api.get('/history/get-history')
    if (Array.isArray(response)) {
      const history = response
      const current = history.find(item => item.status === 'PENDING' || item.status === 'ACTIVE' || item.status === 'IN_USE')
      activeBooking.value = current || null
    }
  } catch (err) { 
    console.error('Lỗi tải session:', err) 
  }
}

async function fetchBookedRooms() {
  if (slot.value === 'Chọn ca học') {
    booked.value = []
    return
  }

  const [year, month, day] = date.value.split('-')
  const formattedDate = `${day}-${month}-${year}`
  const caSo = parseInt(slot.value.match(/\d+/)[0])

  try {
    const response = await api.get(`/booking/get-booked-rooms?date=${formattedDate}&slot=${caSo}`)
    if (Array.isArray(response)) {
      booked.value = response
    }
  } catch (err) { 
    console.error('Lỗi tải phòng đã đặt:', err) 
  }
}

watch([date, slot], () => { fetchBookedRooms() })

const uniqueBuildings = computed(() => ['Tất cả tòa', ...new Set(rooms.value.map(r => r.building))])
const uniqueFloors = computed(() => {
  let filtered = rooms.value
  if (selectedBuilding.value !== 'Tất cả tòa') {
    filtered = filtered.filter(r => r.building === selectedBuilding.value)
  }
  return ['Tất cả tầng', ...new Set(filtered.map(r => r.floor))]
})

const filteredRooms = computed(() => {
  return rooms.value.filter(r => {
    const matchBuilding = selectedBuilding.value === 'Tất cả tòa' || r.building === selectedBuilding.value
    const matchFloor = selectedFloor.value === 'Tất cả tầng' || r.floor === selectedFloor.value
    return matchBuilding && matchFloor
  })
})

const groupedByBuildingAndFloor = computed(() => {
  const groups = {}
  filteredRooms.value.forEach(room => {
    const building = room.building || 'Chưa rõ tòa'
    const floor = room.floor || 'Tầng 1'
    if (!groups[building]) groups[building] = {}
    if (!groups[building][floor]) groups[building][floor] = []
    groups[building][floor].push(room)
  })
  return groups
})

// Xác định trạng thái của từng tủ trên bản đồ
function getCabinetStatus(cab) {
  // 1. Tủ của chính mình đang mượn
  if (activeBooking.value && (activeBooking.value.room === cab.id || activeBooking.value.roomId === cab.id)) {
    return 'MINE'
  }

  // 2. Tủ Offline hoặc đang cài đặt bảo trì -> MAINTENANCE (Đỏ)
  if (cab.status === 'BAO_TRI' || cab.status === 'MAINTENANCE' || cab.isOnline === false) {
    return 'MAINTENANCE'
  }

  if (slot.value === 'Chọn ca học') return 'AVAILABLE'

  // 3. Đã có người đặt trong ca này
  if (booked.value.includes(cab.id) || cab.status === 'BOOKED') return 'BOOKED'

  return 'AVAILABLE'
}

function handleCabinetClick(cab) {
  const status = getCabinetStatus(cab)

  if (status === 'MINE') {
    selectedCabinet.value = cab
    otpValue.value = ''
    return
  }

  if (slot.value === 'Chọn ca học') {
    showMissingSlotModal.value = true
    return
  }

  if (status === 'AVAILABLE') {
    selectedCabinet.value = cab
    otpValue.value = ''
  } else if (status === 'BOOKED') {
    triggerError('Tủ thiết bị này đã có người đăng ký mượn trong ca học này!')
  } else if (status === 'MAINTENANCE') {
    triggerError('Tủ thiết bị này hiện đang mất kết nối hoặc đang được bảo trì!')
  }
}

async function scrollToMyCabinet() {
  if (!activeBooking.value) return triggerError('Bạn hiện không có tủ nào đang mượn!')
  const targetRoom = rooms.value.find(r => r.id === activeBooking.value.room)
  if (targetRoom) {
    selectedBuilding.value = 'Tất cả tòa'
    selectedFloor.value = 'Tất cả tầng'
  }
  await nextTick()
  const el = document.getElementById(`cabinet-${activeBooking.value.room}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    el.classList.add('ring-4', 'ring-amber-500', 'scale-105')
    setTimeout(() => { el.classList.remove('ring-4', 'ring-amber-500', 'scale-105') }, 2000)
  } else {
    triggerError('Không tìm thấy vị trí tủ trên bản đồ!')
  }
}

async function book(room) {
  if (slot.value === 'Chọn ca học') { showMissingSlotModal.value = true; return }
  const [year, month, day] = date.value.split('-')
  const caSo = parseInt(slot.value.match(/\d+/)[0])

  try {
    await api.post('/booking/dat-phong', {
      maPhong: room.id,
      ngayMuon: `${day}-${month}-${year}`,
      caMuon: caSo,
      vaitro: user.value.role === 'Sinh viên' ? 'SINHVIEN' : 'GIANGVIEN'
    })

    showSuccessToast('Đăng ký phòng thành công!')
    selectedCabinet.value = null
    await fetchActiveSession()
    await fetchBookedRooms()
  } catch (err) { 
    triggerError(err.message || 'Không thể kết nối server')
  }
}

async function openDoor() {
  if (!otpValue.value) return triggerError('Vui lòng nhập OTP!')
  try {
    await api.post(`/cabinet/open-door/${activeBooking.value.id}`, {
      otp: otpValue.value
    })
    showSuccessToast('Đã gửi lệnh mở cửa tủ thành công!')
    otpValue.value = ''
    await fetchActiveSession()
  } catch (err) { 
    triggerError(err.message || 'Lỗi kết nối')
  }
}

async function resendOtp() {
  try {
    await api.post(`/history/refresh-otp/${activeBooking.value.id}`)
    showSuccessToast('Đã cấp lại mã OTP mới!')
    otpValue.value = ''
  } catch (err) { 
    triggerError(err.message || 'Lỗi kết nối')
  }
}

async function returnRoom() {
  try {
    await api.put(`/booking/return-room/${activeBooking.value.id}?room=${activeBooking.value.room}`)
    showSuccessToast('Hoàn tất trả thiết bị thành công!')
    confirmReturnId.value = null
    selectedCabinet.value = null
    activeBooking.value = null
    otpValue.value = ''
    await fetchBookedRooms()
    await fetchActiveSession()
  } catch (err) { 
    triggerError(err.message || 'Lỗi kết nối')
  }
}

async function delegateAccess() {
  if (delegateId.value.length !== 8) return triggerError('Mã Sinh viên phải đúng 8 chữ số!')
  try {
    const data = await api.post(`/history/delegate/${activeBooking.value.id}`, {
      delegateId: delegateId.value
    })
    showSuccessToast(data?.message || 'Đã giao quyền thành công!')
    delegateId.value = ''
  } catch (err) { 
    triggerError(err.message || 'Lỗi kết nối tới server!')
  }
}

async function revokeAccess() {
  try {
    await api.post(`/history/revoke/${activeBooking.value.id}`)
    showSuccessToast('Đã thu hồi quyền thành công!')
  } catch (err) { 
    triggerError(err.message || 'Lỗi kết nối tới server!')
  }
}

onMounted(async () => {
  const token = sessionStorage.getItem('classhub-token')
  const saved = sessionStorage.getItem('classhub-user')
  if (saved) {
    user.value = JSON.parse(saved)
    if (user.value.role === "SINHVIEN") user.value.role = "Sinh viên"
    if (user.value.role === "GIANGVIEN") user.value.role = "Giảng viên"
  } else {
    window.location.href = '/login'
    return
  }
  if (!token || !saved) return logout()

  await fetchRooms()
  await fetchActiveSession()
  await fetchBookedRooms()

  // Cập nhật vi phân tại chỗ trên RAM (Delta Update)
  unsubscribeCabinetStatus = cabinetHub.subscribe('CabinetStatusChanged', (data) => {
    const targetRoom = rooms.value.find(r => String(r.id).toLowerCase() === String(data.roomId).toLowerCase())
    if (targetRoom) {
      targetRoom.isOnline = data.isOnline
      if (data.status === 'Bảo trì' || data.isOnline === false) {
        targetRoom.status = 'MAINTENANCE'
      } else {
        targetRoom.status = 'AVAILABLE'
      }
    }

    if (activeBooking.value && String(activeBooking.value.room).toLowerCase() === String(data.roomId).toLowerCase()) {
      activeBooking.value.isCabinetOpen = data.isOpen
    }
  })

  try {
    await cabinetHub.start()
    console.log('Da ket noi Realtime Hub tren Trang chu!')
  } catch (err) {
    console.error('Loi ket noi Realtime:', err)
  }
})

onUnmounted(() => {
  if (unsubscribeCabinetStatus) unsubscribeCabinetStatus()
})
</script>

<template>
  <div v-if="showToast"
    class="fixed bottom-20 right-5 z-[90] rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white shadow-xl">
    {{ toastMessage }}
  </div>
  <div v-if="showErrorToast"
    class="fixed bottom-20 right-5 z-[90] rounded-xl bg-red-600 px-5 py-3 text-sm font-semibold text-white shadow-xl">
    {{ errorMessage }}
  </div>

  <button v-if="activeBooking" @click="scrollToMyCabinet"
    class="fixed bottom-20 right-5 z-[50] flex items-center gap-2 rounded-full bg-amber-500 px-5 py-3 text-sm font-bold text-white shadow-2xl transition-all hover:bg-amber-600 animate-bounce sm:bottom-6">
    <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
      <path stroke-linecap="round" stroke-linejoin="round"
        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
      <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
    Tủ hiện tại ({{ activeBooking.room }})
  </button>

  <div v-if="showMissingSlotModal"
    class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/40 p-5 backdrop-blur-sm"
    @click.self="showMissingSlotModal = false">
    <div class="w-full max-w-sm rounded-3xl bg-white p-6 text-center shadow-2xl">
      <h2 class="text-xl font-bold text-slate-800">Vui lòng chọn ca học trước khi đăng ký</h2>
      <button @click="showMissingSlotModal = false"
        class="mt-6 h-11 w-full rounded-xl bg-blue-600 font-bold text-white transition hover:bg-blue-700">Đã hiểu</button>
    </div>
  </div>

  <div v-if="confirmReturnId"
    class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/40 p-5 backdrop-blur-sm"
    @click.self="confirmReturnId = null">
    <div class="w-full max-w-sm rounded-3xl bg-white p-6 text-center shadow-2xl">
      <h2 class="text-xl font-bold text-slate-800">Xác nhận hoàn tất trả thiết bị</h2>
      <p class="mt-2 text-xs text-slate-500">Hãy đảm bảo bạn đã cất đầy đủ chìa khóa, micro và đóng chặt cửa tủ.</p>
      <div class="mt-6 flex gap-3">
        <button @click="confirmReturnId = null"
          class="h-11 flex-1 rounded-xl border border-blue-100 font-semibold text-slate-500 hover:bg-slate-50">Hủy</button>
        <button @click="returnRoom" class="h-11 flex-1 rounded-xl bg-blue-600 font-bold text-white hover:bg-blue-700">Xác nhận trả</button>
      </div>
    </div>
  </div>

  <div v-if="previewEquipment"
    class="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
    @click.self="previewEquipment = null">
    <div class="w-full max-w-md rounded-3xl bg-white p-6 text-center shadow-2xl">
      <h3 class="text-lg font-bold text-slate-800 mb-4">{{ previewEquipment.name }}</h3>
      <div
        class="overflow-hidden rounded-2xl border border-slate-100 bg-slate-50 flex items-center justify-center min-h-[200px]">
        <img v-if="previewEquipment.image" :src="previewEquipment.image" :alt="previewEquipment.name"
          class="max-h-[300px] w-auto object-contain" />
        <div v-else class="text-slate-400 py-10 font-medium">Chưa có hình ảnh thực tế cho thiết bị này.</div>
      </div>
      <button @click="previewEquipment = null"
        class="mt-6 h-11 w-full rounded-xl bg-blue-600 font-bold text-white hover:bg-blue-700">Đóng</button>
    </div>
  </div>

  <main class="min-h-screen bg-slate-50 pb-20 sm:pb-0">
    <Navbar :user="user" :currentPath="currentPath" @logout="logout" />

    <div class="mx-auto max-w-7xl px-5 py-8 lg:px-8">
      
      <section v-if="activeBooking" class="mb-8 rounded-3xl border border-amber-200 bg-amber-50 p-5 sm:p-6 shadow-sm">
        <h3 class="flex items-center gap-2 text-lg font-bold text-amber-900">
          <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          Ủy quyền mượn / trả thiết bị
        </h3>
        <p class="mt-1 text-xs sm:text-sm text-amber-700">Phiếu mượn phòng <b>{{ activeBooking.room }}</b> đang kích hoạt. Bạn có thể cấp quyền cho 1 sinh viên khác thao tác mở tủ và trả đồ thay mình.</p>
        <div class="mt-4 flex flex-col sm:flex-row gap-3 max-w-2xl">
          <input :value="delegateId" @input="onDelegateInput" type="text" placeholder="Nhập mã SV (8 số)..."
            maxlength="8"
            class="h-11 w-full sm:flex-1 rounded-xl border border-amber-200 px-4 outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500" />
          <div class="flex gap-2 sm:gap-3 w-full sm:w-auto">
            <button @click="delegateAccess"
              class="h-11 flex-1 sm:flex-none rounded-xl bg-amber-600 px-6 font-bold text-white transition hover:bg-amber-700">Giao quyền</button>
            <button @click="revokeAccess"
              class="h-11 flex-1 sm:flex-none rounded-xl border border-amber-600 px-6 font-bold text-amber-700 bg-white transition hover:bg-amber-100">Thu hồi</button>
          </div>
        </div>
      </section>

      <section class="mb-8 rounded-2xl border border-blue-100 bg-white p-4 shadow-lg shadow-blue-100/60 sm:p-5">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label class="grid gap-2 text-sm font-semibold">Ngày mượn 
            <input v-model="date" type="date" class="h-11 rounded-xl border border-blue-100 bg-slate-50 px-3 outline-none focus:ring-2 focus:ring-blue-500" />
          </label>

          <label class="grid gap-2 text-sm font-semibold">Ca học 
            <select v-model="slot" class="h-11 rounded-xl border border-blue-100 bg-slate-50 px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500">
              <option disabled value="Chọn ca học">Chọn ca học</option>
              <option v-for="ca in danhSachCaHoc" :key="ca" :value="ca">{{ ca }}</option>
            </select>
          </label>

          <label class="grid gap-2 text-sm font-semibold">Tòa nhà 
            <select v-model="selectedBuilding" @change="selectedFloor = 'Tất cả tầng'" class="h-11 rounded-xl border border-blue-100 bg-slate-50 px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500">
              <option v-for="b in uniqueBuildings" :key="b" :value="b">{{ b }}</option>
            </select>
          </label>

          <label v-if="selectedBuilding !== 'Tất cả tòa'" class="grid gap-2 text-sm font-semibold animate-fadeIn">Tầng 
            <select v-model="selectedFloor" class="h-11 rounded-xl border border-blue-100 bg-slate-50 px-3 text-sm outline-none focus:ring-2 focus:ring-blue-500">
              <option v-for="f in uniqueFloors" :key="f" :value="f">{{ f }}</option>
            </select>
          </label>
        </div>
      </section>

      <section class="mb-10 rounded-3xl border border-blue-200 bg-white p-6 shadow-sm">
        <div class="mb-8 flex flex-wrap gap-4 border-b border-blue-50 pb-5 text-xs font-semibold text-slate-500">
          <div class="flex items-center gap-2"><span class="size-3 rounded-full bg-emerald-400"></span> Trống / Sẵn sàng</div>
          <div class="flex items-center gap-2"><span class="size-3 rounded-full bg-slate-300"></span> Đã có người mượn</div>
          <div class="flex items-center gap-2"><span class="size-3 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.8)]"></span> Tủ của bạn (Bấm để thao tác)</div>
          <div class="flex items-center gap-2"><span class="size-3 rounded-full bg-red-400"></span> Đang bảo trì / Mất kết nối</div>
        </div>

        <div v-if="Object.keys(groupedByBuildingAndFloor).length === 0" class="py-10 text-center text-slate-400">Không có thiết bị phù hợp bộ lọc.</div>

        <div v-for="(floors, buildingName) in groupedByBuildingAndFloor" :key="buildingName" class="mb-12 last:mb-0">
          <div class="mb-6 flex items-center gap-3 border-b-2 border-blue-500/20 pb-3">
            <div class="flex size-8 items-center justify-center rounded-lg bg-blue-700 text-white shadow-md">
              <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h2 class="text-xl font-black uppercase text-blue-700">{{ buildingName }}</h2>
          </div>

          <div class="flex flex-col-reverse gap-8 px-2 sm:px-4">
            <div v-for="(cabs, floorName) in floors" :key="floorName"
              class="border-b border-dashed border-blue-100 pb-8 last:border-0 last:pb-0">
              <h3 class="mb-5 text-lg font-bold text-slate-400 uppercase tracking-wider">{{ floorName }}</h3>

              <div class="grid grid-cols-3 gap-x-4 gap-y-6 sm:grid-cols-6 lg:grid-cols-8">
                <div v-for="cab in cabs" :key="cab.id" :id="`cabinet-${cab.id}`" @click="handleCabinetClick(cab)"
                  class="relative flex flex-col items-center justify-between p-2 h-32 rounded-md border-b-8 transition-all cursor-pointer hover:-translate-y-1"
                  :class="{
                    'bg-amber-400 border-amber-600 shadow-[0_0_15px_rgba(245,158,11,0.6)] hover:shadow-[0_0_20px_rgba(245,158,11,0.8)] ring-2 ring-amber-500': getCabinetStatus(cab) === 'MINE',
                    'bg-emerald-400 border-emerald-600 hover:shadow-lg': getCabinetStatus(cab) === 'AVAILABLE',
                    'bg-slate-300 border-slate-400 opacity-60 hover:opacity-80': getCabinetStatus(cab) === 'BOOKED',
                    'bg-red-400 border-red-600 opacity-80': getCabinetStatus(cab) === 'MAINTENANCE'
                  }">
                  <div class="w-full bg-white/40 rounded text-center text-[11px] font-black text-slate-800 py-1 shadow-inner truncate px-1">
                    {{ cab.name }}
                  </div>
                  <div class="flex flex-col gap-1 w-full px-3 opacity-30">
                    <div class="h-1 w-full bg-black rounded-full"></div>
                    <div class="h-1 w-full bg-black rounded-full"></div>
                    <div class="h-1 w-full bg-black rounded-full"></div>
                  </div>
                  <div class="absolute right-2 top-12 h-8 w-1.5 bg-white/70 rounded-full shadow-sm"></div>
                  
                  <div v-if="getCabinetStatus(cab) === 'MINE'"
                    class="absolute -top-3 -right-2 bg-white rounded-full p-1.5 shadow-md animate-bounce text-blue-600 ring-2 ring-blue-600">
                    <svg v-if="activeBooking && activeBooking.isCabinetOpen" class="size-4 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round"
                        d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                    <svg v-else class="size-4 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round"
                        d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div v-if="selectedCabinet"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/60 p-4 sm:p-5 backdrop-blur-sm"
      @click.self="selectedCabinet = null; otpValue = ''">
      <div class="w-full max-w-lg rounded-3xl bg-white shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">

        <div class="bg-blue-600 p-5 text-white flex justify-between items-center shrink-0">
          <div>
            <p class="text-xs uppercase tracking-widest text-blue-200">Chi tiết & Thao tác</p>
            <h2 class="text-xl sm:text-2xl font-bold mt-1">Tủ thiết bị {{ selectedCabinet.name }}</h2>
          </div>
          <span v-if="activeBooking && (activeBooking.room === selectedCabinet.id || activeBooking.roomId === selectedCabinet.id) && activeBooking.isCabinetOpen"
            class="animate-pulse rounded-full bg-amber-300 px-3 py-1 text-xs font-bold text-amber-900">TỦ ĐANG MỞ</span>
        </div>

        <div class="p-5 sm:p-6 overflow-y-auto flex-1">
          <p class="mb-3 text-sm font-bold uppercase tracking-wide text-slate-400">Thiết bị có trong tủ (Bấm để xem ảnh)</p>
          <div class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div v-for="item in selectedCabinet.equipment" :key="typeof item === 'object' ? item.name : item"
              @click="previewEquipment = typeof item === 'object' ? item : { name: item, image: '' }"
              class="flex flex-col items-center gap-2 rounded-xl border border-blue-100 bg-slate-50 p-3 text-center cursor-pointer transition hover:border-blue-500 hover:bg-blue-50/50">
              <div
                class="flex size-12 items-center justify-center rounded-lg bg-white overflow-hidden shadow-sm border border-slate-200 text-blue-600 font-bold text-lg">
                {{ typeof item === 'object' ? item.name.charAt(0) : item.charAt(0) }}
              </div>
              <span class="text-xs font-semibold text-slate-800 line-clamp-1">
                {{ typeof item === 'object' ? item.name : item }}
              </span>
            </div>
          </div>

          <template v-if="activeBooking && (activeBooking.room === selectedCabinet.id || activeBooking.roomId === selectedCabinet.id)">
            <div class="border-t border-dashed border-blue-100 pt-6">
              <p class="mb-3 text-sm font-bold uppercase tracking-wide text-slate-400">Thao tác mở khóa</p>
              <div class="mb-6 flex flex-col sm:flex-row gap-2">
                <input v-model="otpValue" type="text" placeholder="Nhập mã OTP..." maxlength="6"
                  class="h-12 w-full sm:flex-1 rounded-xl border border-blue-200 bg-slate-50 px-4 text-center text-lg font-bold tracking-widest text-slate-800 outline-none focus:border-blue-500 focus:ring-2" />
                <div class="flex gap-2 w-full sm:w-auto">
                  <button @click="resendOtp"
                    class="h-12 w-14 sm:w-12 shrink-0 rounded-xl border border-blue-200 text-slate-500 hover:bg-blue-50 flex items-center justify-center"
                    title="Gửi lại OTP">
                    <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  </button>
                  <button @click="openDoor"
                    class="h-12 flex-1 sm:flex-none shrink-0 rounded-xl bg-slate-900 px-6 font-bold text-white transition hover:bg-slate-800">
                    Mở Khóa
                  </button>
                </div>
              </div>
              <button @click="confirmReturnId = activeBooking.id"
                class="h-12 w-full rounded-xl border-2 border-blue-600 font-bold text-blue-600 hover:bg-blue-600 hover:text-white transition">
                Cất đồ &amp; Hoàn tất trả
              </button>
            </div>
          </template>

          <template v-else>
            <div class="border-t border-dashed border-blue-100 pt-6">
              <div class="flex gap-2 items-center text-sm text-slate-500 mb-4">
                <svg class="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Đăng ký cho <b>{{ date }}</b> lúc <b>{{ slot }}</b></span>
              </div>
              <button @click="book(selectedCabinet)"
                class="h-12 w-full rounded-xl bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700 shadow-md">
                Đăng ký mượn ngay
              </button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <BottomNav :currentPath="currentPath" :is-admin="user.role === 'ADMIN'" />
  </main>
</template>
