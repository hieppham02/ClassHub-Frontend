<script setup>
import AppModal from '@/components/shared/AppModal.vue'
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import Navbar from '@/components/shared/Navbar.vue'
import BottomNav from '@/components/shared/BottomNav.vue'
import OperationsPanel from '@/components/shared/OperationsPanel.vue'
import { api } from '@/services/apiClient.js'
import { cabinetHub } from '@/services/cabinetHub.js'

const currentPath = ref(window.location.pathname)
const user = ref({ name: '', role: '' })

const rooms = ref([])
const activeBooking = ref(null)
const booked = ref([])

const date = ref(new Date().toLocaleDateString('en-CA'))
const slot = ref('Chọn ca học')
const slots = ref([])
const danhSachCaHoc = computed(() => slots.value.map(ca => `${ca.name} (${ca.start} - ${ca.end})`))
const selectedSlotId = computed(() => slots.value[danhSachCaHoc.value.indexOf(slot.value)]?.id)
const returnCondition = ref('BINH_THUONG')
const returnNote = ref('')
const returning = ref(false)
let sessionTimer
async function fetchSlots() {
  try { slots.value = await api.get('/operations/slots') }
  catch (err) { triggerError(err.message || 'Không tải được ca học.') }
}
const selectedBuilding = ref('Tất cả tòa')
const selectedFloor = ref('Tất cả tầng')

const selectedCabinet = ref(null)
const showDamageReport = ref(false)
const damageLocationId = ref('')
const damageBuilding = ref('')
const damageFloor = ref('')
const damageBuildings = computed(() => [...new Set(rooms.value.map(r => r.building))])
const damageFloors = computed(() => [...new Set(rooms.value.filter(r => !damageBuilding.value || r.building === damageBuilding.value).map(r => r.floor))].sort((a, b) => a.localeCompare(b, 'vi', { numeric: true })))
const damageLocations = computed(() => rooms.value.filter(r => (!damageBuilding.value || r.building === damageBuilding.value) && (!damageFloor.value || r.floor === damageFloor.value)))
watch(damageBuilding, () => { damageFloor.value = ''; damageLocationId.value = '' })
watch(damageFloor, () => { damageLocationId.value = '' })
const damageEquipment = ref('')
const damageDescription = ref('')
const sendingDamage = ref(false)
function openDamageReport() {
  showDamageReport.value = true
  damageLocationId.value = ''
  damageBuilding.value = selectedBuilding.value === 'Tất cả tòa' ? '' : selectedBuilding.value
  damageFloor.value = ''
  damageEquipment.value = ''; damageDescription.value = ''
}
async function sendDamageReport() {
  if (sendingDamage.value) return
  sendingDamage.value = true
  try {
    await api.post('/damage-reports', { roomId: damageLocationId.value, equipmentName: damageEquipment.value.trim(), description: damageDescription.value.trim() })
    showDamageReport.value = false
    showSuccessToast('Đã gửi báo cáo hỏng hóc cho quản trị viên.')
  } catch (err) { triggerError(err.message || 'Không gửi được báo cáo.') }
  finally { sendingDamage.value = false }
}

const otpValue = ref('')
const delegateId = ref('')
const confirmReturnId = ref(null)
const showMissingSlotModal = ref(false)
const showToast = ref(false)
const toastMessage = ref('')
const showErrorToast = ref(false)
const errorMessage = ref('')
const previewEquipment = ref(null)
const isLoadingRooms = ref(true)

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
  isLoadingRooms.value = true
  try {
    const response = await api.get('/rooms/get-rooms')
    if (Array.isArray(response)) {
      rooms.value = response
      rooms.value.forEach(r => {
        if (!r.equipment) r.equipment = []
        if (!r.floor) r.floor = 'Tầng 1'
        if (!r.building) r.building = 'Tòa EAUT'
      })
    }
  } catch (err) { 
    console.error('Lỗi tải phòng:', err) 
  } finally {
    isLoadingRooms.value = false
  }
}

async function fetchActiveSession() {
  try {
    const response = await api.get('/history/get-history')
    if (Array.isArray(response)) {
      const history = response
      const current = history.find(item => item.status === 'PENDING' || item.status === 'ACTIVE' || item.status === 'IN_USE' || item.status === 'RETURNING')
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
  const caSo = selectedSlotId.value

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
  Object.values(groups).forEach(floors => {
    Object.values(floors).forEach(cabinets => {
      cabinets.sort((a, b) => Number(b.locationType === 'CORRIDOR') - Number(a.locationType === 'CORRIDOR'))
    })
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
  const caSo = selectedSlotId.value

  try {
    await api.post('/booking/dat-phong', {
      maPhong: room.id,
      ngayMuon: `${day}-${month}-${year}`,
      caMuon: caSo
    })

    showSuccessToast(room.locationType === 'CORRIDOR' ? 'Đăng ký mượn tủ hành lang thành công!' : 'Đăng ký phòng thành công!')
    selectedCabinet.value = null
    await fetchActiveSession()
    await fetchBookedRooms()
  } catch (err) { 
    triggerError(err.message || 'Không thể kết nối server')
  }
}

async function openDoor() {
  if (activeBooking.value?.status === 'RETURNING') return triggerError('Phiếu đang chờ kiểm tra trả; không thể mở tủ bằng OTP.')
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
  if (activeBooking.value?.status === 'RETURNING') return triggerError('Phiếu đang chờ kiểm tra trả; không cấp lại OTP.')
  try {
    await api.post(`/history/refresh-otp/${activeBooking.value.id}`)
    showSuccessToast('Đã cấp lại mã OTP mới!')
    otpValue.value = ''
  } catch (err) { 
    triggerError(err.message || 'Lỗi kết nối')
  }
}

async function returnRoom() {
  if (returning.value || !activeBooking.value) return
  if (!['ACTIVE', 'IN_USE', 'RETURNING'].includes(activeBooking.value.status)) return triggerError('Chỉ trả phiên đã nhận thiết bị.')
  returning.value = true
  try {
    if (activeBooking.value.status !== 'RETURNING') {
      await api.put(`/operations/sessions/${activeBooking.value.id}/return-report`, { condition: returnCondition.value, note: returnNote.value })
    }
    await api.put(`/booking/return-room/${activeBooking.value.id}?room=${activeBooking.value.room}`)
    showSuccessToast('Đã yêu cầu khóa tủ. Phiếu chờ quản trị viên kiểm tra trả.')
    confirmReturnId.value = null
    selectedCabinet.value = null
    otpValue.value = ''
    await fetchBookedRooms()
    await fetchActiveSession()
  } catch (err) { 
    triggerError(err.message || 'Lỗi kết nối')
  } finally { returning.value = false }
}

async function delegateAccess() {
  if (activeBooking.value?.status === 'RETURNING') return triggerError('Phiếu đang chờ kiểm tra trả; không thể ủy quyền.')
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

  await fetchSlots()
  await fetchRooms()
  await fetchActiveSession()
  await fetchBookedRooms()

  sessionTimer = setInterval(fetchActiveSession, 30000)

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
  clearInterval(sessionTimer)
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

  <AppModal v-if="showMissingSlotModal" title="Chọn ca học" @close="showMissingSlotModal = false">
    <p class="text-sm leading-relaxed text-slate-500">Vui lòng chọn ca học trước khi đăng ký mượn thiết bị.</p>
    <template #footer><button type="button" @click="showMissingSlotModal = false" class="modal-primary">Đã hiểu</button></template>
  </AppModal>

  <AppModal v-if="confirmReturnId" title="Gửi yêu cầu trả thiết bị" :busy="returning" @close="confirmReturnId = null">
    <div class="space-y-4">
      <p class="text-sm leading-relaxed text-slate-500">Hãy đảm bảo bạn đã cất đầy đủ chìa khóa, micro và đóng chặt cửa tủ.</p>
      <div>
        <label class="modal-label" for="return-condition">Tình trạng trả</label>
        <select id="return-condition" v-model="returnCondition" class="modal-field">
          <option value="BINH_THUONG">Bình thường</option><option value="HONG_HOC">Có hỏng hóc</option><option value="MAT_DO">Thiếu thiết bị</option>
        </select>
      </div>
      <div>
        <label class="modal-label" for="return-note">Ghi chú</label>
        <textarea id="return-note" v-model="returnNote" maxlength="2000" placeholder="Mô tả thiết bị hỏng/thiếu" class="modal-field" />
      </div>
    </div>
    <template #footer>
      <button type="button" :disabled="returning" @click="confirmReturnId = null" class="modal-cancel">Hủy</button>
      <button type="button" :disabled="returning" @click="returnRoom" class="modal-primary">Xác nhận trả</button>
    </template>
  </AppModal>

  <AppModal v-if="previewEquipment" :title="previewEquipment.name" size="md" layer="nested" @close="previewEquipment = null">
    <div class="flex min-h-[200px] items-center justify-center overflow-hidden rounded-xl border border-blue-100 bg-blue-50/30">
      <img v-if="previewEquipment.image" :src="previewEquipment.image" :alt="previewEquipment.name" class="max-h-[300px] max-w-full object-contain" />
      <p v-else class="px-4 py-10 text-center text-sm text-slate-500">Chưa có hình ảnh thực tế cho thiết bị này.</p>
    </div>
    <template #footer><button type="button" @click="previewEquipment = null" class="modal-cancel">Đóng</button></template>
  </AppModal>

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

      <section class="mb-10 rounded-3xl border border-blue-200 bg-white p-4 sm:p-6 shadow-sm">
        <div class="mb-6 flex flex-wrap items-center gap-2 sm:gap-3 border-b border-blue-50 pb-4 text-xs font-semibold text-slate-500">
          <div class="inline-flex items-center gap-1.5 rounded-lg bg-slate-50 border border-slate-100 px-2.5 py-1">
            <span class="size-2.5 rounded-full bg-emerald-500"></span>
            <span>Trống / Sẵn sàng</span>
          </div>
          <div class="inline-flex items-center gap-1.5 rounded-lg bg-slate-50 border border-slate-100 px-2.5 py-1">
            <span class="size-2.5 rounded-full bg-slate-300"></span>
            <span>Đã có người mượn</span>
          </div>
          <div class="inline-flex items-center gap-1.5 rounded-lg bg-amber-50 border border-amber-200 px-2.5 py-1 text-amber-900">
            <span class="size-2.5 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)]"></span>
            <span>Tủ của bạn</span>
          </div>
          <div class="inline-flex items-center gap-1.5 rounded-lg bg-red-50 border border-red-100 px-2.5 py-1 text-red-700">
            <span class="size-2.5 rounded-full bg-red-500"></span>
            <span>Bảo trì / Mất kết nối</span>
          </div>
          <button type="button" @click="openDamageReport" class="ml-auto inline-flex h-9 items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 text-xs font-semibold text-red-700 transition hover:bg-red-100">Báo hỏng hóc</button>
        </div>

        <!-- Skeleton Loading State khi tải danh sách tủ -->
        <div v-if="isLoadingRooms" class="py-4">
          <div class="mb-6 flex items-center gap-3">
            <div class="size-8 rounded-lg bg-slate-200 animate-pulse"></div>
            <div class="h-6 w-36 bg-slate-200 animate-pulse rounded-lg"></div>
          </div>
          <div class="grid grid-cols-2 min-[440px]:grid-cols-3 sm:grid-cols-6 lg:grid-cols-8 gap-3 sm:gap-x-4 sm:gap-y-6">
            <div
              v-for="i in 8"
              :key="`skel-cab-${i}`"
              class="relative flex flex-col justify-between p-2.5 h-28 sm:h-32 rounded-xl bg-slate-100 border border-slate-200 animate-pulse"
            >
              <div class="h-5 w-3/4 mx-auto bg-slate-200/80 rounded-lg"></div>
              <div class="flex flex-col gap-1.5 px-2">
                <div class="h-1 w-full bg-slate-200/70 rounded-full"></div>
                <div class="h-1 w-full bg-slate-200/70 rounded-full"></div>
                <div class="h-1 w-full bg-slate-200/70 rounded-full"></div>
              </div>
              <div class="h-3 w-1/2 mx-auto bg-slate-200/50 rounded"></div>
            </div>
          </div>
        </div>

        <div v-else-if="Object.keys(groupedByBuildingAndFloor).length === 0" class="py-12 text-center text-slate-400">
          <svg class="size-10 mx-auto text-slate-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p class="text-sm font-medium">Không tìm thấy thiết bị phù hợp với bộ lọc</p>
        </div>

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

          <div class="flex flex-col-reverse gap-8 px-1 sm:px-4">
            <div v-for="(cabs, floorName) in floors" :key="floorName"
              class="border-b border-dashed border-blue-100 pb-8 last:border-0 last:pb-0">
              <h3 class="mb-4 text-sm sm:text-base font-bold text-slate-400 uppercase tracking-wider">{{ floorName }}</h3>

              <div class="grid grid-cols-2 min-[440px]:grid-cols-3 sm:grid-cols-6 lg:grid-cols-8 gap-3 sm:gap-x-4 sm:gap-y-6">
                <div v-for="cab in cabs" :key="cab.id" :id="`cabinet-${cab.id}`" @click="handleCabinetClick(cab)"
                  class="relative flex flex-col items-center justify-between p-2.5 h-28 sm:h-32 rounded-xl border-b-8 transition-all cursor-pointer select-none hover:-translate-y-1 active:scale-[0.97]"
                  :class="{
                    'bg-amber-400 border-amber-600 shadow-[0_0_15px_rgba(245,158,11,0.6)] hover:shadow-[0_0_20px_rgba(245,158,11,0.8)] ring-2 ring-amber-500': getCabinetStatus(cab) === 'MINE',
                    'bg-emerald-400 border-emerald-600 hover:shadow-lg': getCabinetStatus(cab) === 'AVAILABLE',
                    'bg-slate-300 border-slate-400 opacity-60 hover:opacity-80': getCabinetStatus(cab) === 'BOOKED',
                    'bg-red-400 border-red-600 opacity-80': getCabinetStatus(cab) === 'MAINTENANCE'
                  }">
                  <div class="w-full bg-white/70 backdrop-blur-xs rounded-lg text-center text-xs font-black text-slate-800 py-1.5 shadow-xs truncate px-1.5">
                    {{ cab.name }}
                  </div>
                  <div v-if="cab.locationType === 'CORRIDOR'" class="corridor-doors" aria-hidden="true"><span></span><span></span></div>
                  <div v-else class="flex flex-col gap-1 w-full px-2 sm:px-3 opacity-30">
                    <div class="h-1 w-full bg-black rounded-full"></div>
                    <div class="h-1 w-full bg-black rounded-full"></div>
                    <div class="h-1 w-full bg-black rounded-full"></div>
                  </div>
                  <div class="absolute right-2 sm:right-2.5 top-1/2 -translate-y-1/2 h-7 sm:h-8 w-1.5 bg-white/80 rounded-full shadow-xs"></div>
                  
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

    <AppModal v-if="showDamageReport" title="Báo cáo hỏng hóc" layer="nested" :busy="sendingDamage" @close="showDamageReport = false">
      <form id="damage-report-form" @submit.prevent="sendDamageReport" class="space-y-4">
        <div class="grid grid-cols-2 gap-3">
          <label class="block text-sm font-semibold">Tòa
            <select v-model="damageBuilding" class="modal-field mt-2 w-full">
              <option value="">Tất cả tòa</option>
              <option v-for="name in damageBuildings" :key="name" :value="name">{{ name }}</option>
            </select>
          </label>
          <label class="block text-sm font-semibold">Tầng
            <select v-model="damageFloor" class="modal-field mt-2 w-full">
              <option value="">Tất cả tầng</option>
              <option v-for="name in damageFloors" :key="name" :value="name">{{ name }}</option>
            </select>
          </label>
        </div>
        <label class="block text-sm font-semibold">Phòng / tủ cần báo hỏng
          <select v-model="damageLocationId" required class="modal-field mt-2 w-full">
            <option disabled value="">Chọn phòng hoặc tủ hành lang</option>
            <option v-for="location in damageLocations" :key="location.id" :value="location.id">{{ location.name }} · {{ location.floor }} · {{ location.building }}</option>
          </select>
        </label>
        <p v-if="!damageLocations.length" class="text-xs text-slate-500">Không có phòng/tủ phù hợp với tòa và tầng đã chọn.</p>
        <label class="block text-sm font-semibold">Thiết bị hỏng<input v-model="damageEquipment" required maxlength="100" class="modal-field mt-2 w-full" placeholder="Ví dụ: ổ điện, máy chiếu..." /></label>
        <label class="block text-sm font-semibold">Mô tả hỏng hóc<textarea v-model="damageDescription" required minlength="10" maxlength="2000" rows="5" class="modal-field mt-2 w-full" placeholder="Mô tả hiện tượng và vị trí thiết bị..." /></label>
        <p class="text-xs text-slate-500">Báo cáo sẽ được gửi cho quản trị viên để kiểm tra và xử lý.</p>
      </form>
      <template #footer><button class="modal-cancel" :disabled="sendingDamage" @click="showDamageReport = false">Hủy</button><button form="damage-report-form" type="submit" class="modal-primary" :disabled="sendingDamage">{{ sendingDamage ? 'Đang gửi...' : 'Gửi báo cáo' }}</button></template>
    </AppModal>
    <AppModal v-if="selectedCabinet" :title="selectedCabinet.locationType === 'CORRIDOR' ? selectedCabinet.name : 'Tủ thiết bị ' + selectedCabinet.name" size="lg" layer="cabinet" @close="selectedCabinet = null; otpValue = ''">
      <template #subtitle>
        <span v-if="activeBooking && (activeBooking.room === selectedCabinet.id || activeBooking.roomId === selectedCabinet.id) && activeBooking.isCabinetOpen" class="mt-2 inline-flex rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-800">Tủ đang mở</span>
      </template>
      
          <p v-if="activeBooking?.status === 'RETURNING' && activeBooking.room === selectedCabinet.id" class="mb-4 rounded-xl bg-amber-50 p-3 text-sm">Phiếu đang chờ kiểm tra trả. Nếu gửi lệnh khóa thất bại, có thể gửi lại yêu cầu trả.</p>
          <ul v-if="selectedCabinet.equipmentDetails?.length" class="mb-4 space-y-2 text-sm">
            <li v-for="item in selectedCabinet.equipmentDetails" :key="item.id">{{ item.name }} × {{ item.quantity }} · {{ { TOT: 'Tốt', HONG: 'Hỏng', DANG_BAO_TRI: 'Đang bảo trì' }[item.condition] || item.condition }}<p v-if="item.note" class="text-xs text-slate-500">{{ item.note }}</p></li>
          </ul>
          <p class="mb-3 text-sm font-bold uppercase tracking-wide text-slate-400">{{ selectedCabinet.locationType === 'CORRIDOR' ? 'Đồ dùng chung · Hành lang' : 'Danh mục thiết bị của phòng' }}</p>
          <p v-if="selectedCabinet.locationType === 'CORRIDOR'" class="mb-4 text-sm text-slate-500">Ổ điện, cáp mạng LAN, phấn viết bảng. Quy trình mượn và trả giống tủ phòng học.</p>
          <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 sm:grid-cols-3">
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
                  class="modal-field" />
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
                    class="modal-primary">
                    Mở Khóa
                  </button>
                </div>
              </div>
              <button @click="confirmReturnId = activeBooking.id"
                class="modal-cancel w-full">
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
                class="modal-primary w-full">
                Đăng ký mượn ngay
              </button>
            </div>
          </template>
      <template #footer><button type="button" @click="selectedCabinet = null; otpValue = ''" class="modal-cancel">Đóng</button></template>
    </AppModal>

    <div class="mx-auto max-w-7xl px-4"><OperationsPanel /></div>
    <BottomNav :currentPath="currentPath" :is-admin="user.role === 'ADMIN'" />
  </main>
</template>

<style scoped>
.corridor-doors { display: flex; gap: 4px; width: 88%; height: 38px; }
.corridor-doors span { flex: 1; border: 2px solid #ffffff90; border-radius: 6px; position: relative; }
.corridor-doors span::after { content: ''; position: absolute; right: 5px; top: 30%; height: 14px; width: 3px; background: white; border-radius: 4px; }
</style>
