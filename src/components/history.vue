<script setup>
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import BottomNav from '@/components/BottomNav.vue'
import { api } from '@/services/apiClient.js'

const history = ref([])
const user = ref({ name: '', role: '' })
const currentPath = ref(window.location.pathname)

function logout() {
  sessionStorage.removeItem('classhub-token')
  sessionStorage.removeItem('classhub-user')
  window.location.href = '/login'
}

// Hàm format thời gian thông minh: Chỉ lấy HH:mm
function formatTime(dateTimeStr) {
  if (!dateTimeStr || dateTimeStr === '---') return '---'
  
  // Nếu BE trả về chuỗi ISO (VD: "2026-08-24T14:30:00")
  try {
    const d = new Date(dateTimeStr)
    // Kiểm tra xem parse ngày hợp lệ không
    if (!isNaN(d.getTime())) {
      return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
    }
  } catch (e) {}

  // Nếu BE tự parse ra chuỗi có chứa dấu cách (VD: "24-08-2026 14:30")
  if (dateTimeStr.includes(' ')) {
    const parts = dateTimeStr.split(' ')
    return parts[parts.length - 1] // Lấy mẩu cuối cùng (chứa giờ)
  }

  // Nếu BE đã trả về chuẩn "14:30" rồi thì trả ra nguyên gốc
  return dateTimeStr
}

async function fetchHistory() {
  try {
    history.value = await api.get('/history/get-history')
  } catch (err) { console.error('Lỗi khi lấy lịch sử:', err) }
}

onMounted(() => {
  const token = sessionStorage.getItem('classhub-token')
  const saved = sessionStorage.getItem('classhub-user')
  if (!token || !saved) return logout()
  user.value = JSON.parse(saved)
  if (user.value.role === "SINHVIEN") user.value.role = "Sinh viên"
  if (user.value.role === "GIANGVIEN") user.value.role = "Giảng viên"
  fetchHistory()
})
</script>

<template>
  <main class="min-h-screen bg-mist pb-20 sm:pb-0">
    <Navbar :user="user" :currentPath="currentPath" @logout="logout" />

    <div class="mx-auto max-w-4xl px-5 py-12 lg:px-8">
      <h1 class="mt-2 text-3xl sm:text-4xl font-bold text-ink">Lịch sử mượn phòng & Thiết bị</h1>
      
      <div v-if="!history.length" class="mt-10 rounded-3xl border border-dashed border-blue-200 bg-white p-12 text-center">
        <h2 class="text-lg font-bold text-ink">Chưa có lượt mượn nào</h2>
      </div>

      <div v-else class="mt-8 grid gap-4">
        <!-- Vòng lặp lịch sử -->
        <div v-for="item in history" :key="item.id" class="flex flex-col gap-4 rounded-2xl border border-blue-100 bg-white p-6 shadow-sm">
          
          <!-- Dòng trên: Tên phòng & Trạng thái -->
          <div class="flex items-center justify-between border-b border-blue-50 pb-4">
            <div>
              <p class="text-lg font-bold text-ink">{{ item.name }} <span class="text-xs font-normal text-slate-400">({{ item.building }})</span></p>
              <p class="text-xs text-slate-500 mt-0.5">Ca học: <b>{{ item.slot }}</b> · Ngày: {{ item.date }}</p>
            </div>
            <div>
              <span v-if="item.status === 'COMPLETED'" class="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-bold text-slate-600">ĐÃ TRẢ</span>
              <span v-else-if="item.status === 'CANCELED'" class="rounded-full bg-red-50 px-3 py-1 text-[11px] font-bold text-red-600">ĐÃ HỦY</span>
              <span v-else class="rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-bold text-emerald-600">ĐANG MƯỢN</span>
            </div>
          </div>

          <!-- Dòng dưới: Chi tiết Người mượn / Trả & Thời gian -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-600">
            <div class="flex items-center gap-2">
              <span class="font-semibold text-slate-400">Người mượn:</span>
              <span class="font-bold text-ink">{{ item.borrowerName || user.name }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-semibold text-slate-400">Mượn lúc:</span>
              <!-- Dùng hàm formatTime để cắt chuỗi lấy giờ:phút -->
              <span class="font-medium">{{ formatTime(item.createdAt) || '---' }}</span>
            </div>
            
            <div class="flex items-center gap-2">
              <span class="font-semibold text-slate-400">Người trả:</span>
              <span :class="item.returnerName ? 'font-bold text-ink' : 'font-medium text-slate-400'">
                {{ item.returnerName || 'Chưa trả' }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-semibold text-slate-400">Trả lúc:</span>
              <!-- Dùng hàm formatTime để cắt chuỗi lấy giờ:phút -->
              <span class="font-medium">{{ formatTime(item.returnedAt) || '---' }}</span>
            </div>
          </div>

        </div>
      </div>
    </div>

    <BottomNav :currentPath="currentPath" :is-admin="user.role === 'ADMIN'" />
  </main>
</template>
