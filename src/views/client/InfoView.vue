<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/shared/Navbar.vue'
import BottomNav from '@/components/shared/BottomNav.vue'
import { api } from '@/services/apiClient.js'

const router = useRouter()
const user = ref({
  ma_sv: '',
  id: '',
  name: '',
  role: '',
  email: '',
  phone: '',
  ten_lop: '',
  className: '',
  classOrDept: '',
  isActive: true
})
const currentPath = ref('/info')
const showLogoutModal = ref(false)
const copiedField = ref('')
const history = ref([])
const statsLoading = ref(true)
const statsError = ref('')
const borrowCount = computed(() => history.value.filter(item =>
  ['ACTIVE', 'IN_USE', 'RETURNING', 'COMPLETED'].includes(item.status)
).length)
const heldCabinets = computed(() => [...new Map(history.value
  .filter(item => ['ACTIVE', 'IN_USE', 'RETURNING'].includes(item.status))
  .map(item => [item.room, item])).values()])

async function fetchStats() {
  statsLoading.value = true
  statsError.value = ''
  try {
    const data = await api.get('/history/get-history')
    if (!Array.isArray(data)) throw new Error('Lịch sử không hợp lệ')
    history.value = data
  } catch {
    statsError.value = 'Chưa tải được thống kê mượn trả.'
  } finally {
    statsLoading.value = false
  }
}

const userIdentifier = computed(() => {
  return user.value?.ma_sv || user.value?.id || user.value?.username || '---'
})

const userClassOrDept = computed(() => {
  return user.value?.ten_lop || user.value?.className || user.value?.classOrDept || '---'
})

const rawRole = computed(() => (user.value?.role || '').toUpperCase())
const isAdmin = computed(() => rawRole.value === 'ADMIN')

const roleDisplay = computed(() => {
  const r = rawRole.value
  if (r === 'ADMIN') return 'Quản trị viên'
  if (r === 'GIANGVIEN' || r === 'GIẢNG VIÊN') return 'Giảng viên'
  if (r === 'SINHVIEN' || r === 'SINH VIÊN') return 'Sinh viên'
  return user.value?.role || 'Người dùng'
})

const initialLetter = computed(() => {
  const name = user.value?.name?.trim()
  if (!name) return 'U'
  const parts = name.split(/\s+/)
  return parts[parts.length - 1].charAt(0).toUpperCase() || 'U'
})

onMounted(() => {
  currentPath.value = window.location.pathname
  const saved = sessionStorage.getItem('classhub-user')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      user.value = { ...user.value, ...parsed }
    } catch {
      logout()
      return
    }
  } else {
    router.push('/login')
    return
  }
  fetchStats()
})

function copyText(val, fieldName) {
  if (!val || val === '---') return
  navigator.clipboard?.writeText(val)
  copiedField.value = fieldName
  setTimeout(() => {
    copiedField.value = ''
  }, 1800)
}

function confirmLogout() {
  showLogoutModal.value = true
}

function cancelLogout() {
  showLogoutModal.value = false
}

function logout() {
  sessionStorage.removeItem('classhub-token')
  sessionStorage.removeItem('classhub-user')
  window.location.href = '/login'
}
</script>

<template>
  <main class="min-h-[100dvh] bg-mist pb-24 sm:pb-12 text-ink">
    <Navbar :user="user" :currentPath="currentPath" @logout="confirmLogout" />

    <section class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-8">

      <!-- Eyebrow & Title -->
      <div class="mb-6">
        <p class="text-xs font-bold uppercase tracking-wide text-brand">TÀI KHOẢN &amp; HỆ THỐNG</p>
        <h1 class="mt-1 text-2xl sm:text-3xl font-black text-ink">Hồ sơ người dùng</h1>
        <p class="mt-1 text-xs sm:text-sm text-slate-500">Quản lý thông tin định danh và phiên làm việc ClassHub.</p>
      </div>

      <!-- Main Profile Card -->
      <div class="overflow-hidden rounded-3xl border border-blue-100 bg-white shadow-sm">

        <!-- Hero Profile Banner -->
        <div class="relative bg-gradient-to-r from-brand-dark via-brand to-blue-600 p-6 sm:p-8 text-white">
          <div class="relative z-10 flex flex-col sm:flex-row sm:items-center gap-5">
            <!-- Avatar -->
            <div class="flex size-20 sm:size-24 shrink-0 items-center justify-center rounded-2xl bg-white/20 text-3xl sm:text-4xl font-black text-white ring-4 ring-white/30 backdrop-blur-md shadow-md">
              {{ initialLetter }}
            </div>

            <!-- Basic Info -->
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <span class="inline-flex items-center rounded-full bg-white/20 px-3 py-0.5 text-xs font-bold text-white ring-1 ring-white/30 backdrop-blur-sm">
                  {{ roleDisplay }}
                </span>
                <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-400/25 px-2.5 py-0.5 text-xs font-semibold text-emerald-100 ring-1 ring-emerald-300/40">
                  <span class="size-1.5 rounded-full bg-emerald-300 animate-pulse"></span>
                  Đang hoạt động
                </span>
              </div>
              <h2 class="mt-2 text-xl sm:text-2xl font-black truncate text-white">{{ user.name || 'Người dùng' }}</h2>
              <p class="mt-0.5 text-xs sm:text-sm text-blue-100 truncate">{{ user.email || 'Chưa liên kết email' }}</p>
            </div>
          </div>
        </div>

        <!-- Information List -->
        <div class="p-6 sm:p-8 space-y-6">
          <div>
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Chi tiết tài khoản</h3>
            <div class="divide-y divide-blue-50 rounded-2xl border border-blue-100 bg-slate-50/50">

              <!-- Họ và tên -->
              <div class="flex items-center justify-between p-4 text-sm">
                <span class="text-xs font-semibold text-slate-500">Họ và tên</span>
                <span class="font-bold text-ink">{{ user.name || '---' }}</span>
              </div>

              <!-- Mã định danh -->
              <div class="flex items-center justify-between p-4 text-sm">
                <span class="text-xs font-semibold text-slate-500">MSSV / MSGV</span>
                <div class="flex items-center gap-2">
                  <span class="font-bold text-ink">{{ userIdentifier }}</span>
                  <button
                    v-if="userIdentifier && userIdentifier !== '---'"
                    @click="copyText(userIdentifier, 'id')"
                    class="rounded-lg p-1 text-slate-400 hover:bg-white hover:text-brand transition active:scale-95"
                    title="Sao chép mã"
                  >
                    <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                  <span v-if="copiedField === 'id'" class="text-[10px] font-bold text-brand">Đã sao chép!</span>
                </div>
              </div>

              <!-- Email -->
              <div class="flex items-center justify-between p-4 text-sm">
                <span class="text-xs font-semibold text-slate-500">Email trường</span>
                <div class="flex items-center gap-2">
                  <span class="font-medium text-slate-700 truncate max-w-[200px] sm:max-w-none">{{ user.email || '---' }}</span>
                  <button
                    v-if="user.email"
                    @click="copyText(user.email, 'email')"
                    class="rounded-lg p-1 text-slate-400 hover:bg-white hover:text-brand transition active:scale-95"
                    title="Sao chép email"
                  >
                    <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                  <span v-if="copiedField === 'email'" class="text-[10px] font-bold text-brand">Đã sao chép!</span>
                </div>
              </div>

              <!-- Lớp / Đơn vị -->
              <div class="flex items-center justify-between p-4 text-sm">
                <span class="text-xs font-semibold text-slate-500">Lớp / Bộ môn / Khoa</span>
                <span class="font-bold text-ink">{{ userClassOrDept }}</span>
              </div>

              <!-- Vai trò -->
              <div class="flex items-center justify-between p-4 text-sm">
                <span class="text-xs font-semibold text-slate-500">Vai trò</span>
                <span class="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-bold text-brand">{{ roleDisplay }}</span>
              </div>

              <!-- Số điện thoại nếu có -->
              <div v-if="user.phone" class="flex items-center justify-between p-4 text-sm">
                <span class="text-xs font-semibold text-slate-500">Số điện thoại</span>
                <span class="font-medium text-slate-700">{{ user.phone }}</span>
              </div>
            </div>
          </div>

          <div aria-live="polite" :aria-busy="statsLoading">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Thống kê mượn trả</h3>
            <p v-if="statsLoading" class="text-sm text-slate-500">Đang tải thống kê…</p>
            <div v-else-if="statsError" class="flex flex-wrap items-center gap-3 text-sm">
              <p class="text-slate-500">{{ statsError }}</p>
              <button @click="fetchStats" class="min-h-11 rounded-xl border border-blue-100 px-4 font-semibold text-brand hover:bg-blue-50">Thử lại</button>
            </div>
            <template v-else>
              <div class="grid grid-cols-2 gap-3">
                <div class="rounded-2xl border border-blue-100 bg-blue-50/50 p-4">
                  <p class="text-2xl font-black text-brand">{{ borrowCount }}</p>
                  <p class="mt-1 text-xs text-slate-500">Lượt mượn đã thực hiện</p>
                </div>
                <div class="rounded-2xl border border-blue-100 bg-blue-50/50 p-4">
                  <p class="text-2xl font-black text-brand">{{ heldCabinets.length }}</p>
                  <p class="mt-1 text-xs text-slate-500">Tủ đang giữ</p>
                </div>
              </div>
              <p class="mt-3 text-xs text-slate-500">Bao gồm lượt mượn được ủy quyền; không tính phiếu chờ hoặc đã hủy.</p>
              <ul v-if="heldCabinets.length" class="mt-3 space-y-2">
                <li v-for="cabinet in heldCabinets" :key="cabinet.room" class="rounded-xl border border-blue-100 px-4 py-3 text-sm text-slate-700">
                  <span class="font-bold text-ink">{{ cabinet.name || cabinet.room }}</span> · {{ cabinet.building }}
                </li>
              </ul>
            </template>
          </div>

          <!-- Quick Actions Grid -->
          <div>
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Lối tắt tác vụ</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">

              <!-- Link to History -->
              <router-link
                to="/history"
                class="flex items-center gap-3.5 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm transition hover:border-brand hover:shadow-md active:scale-[0.98]"
              >
                <div class="flex size-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-brand">
                  <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-bold text-ink">Lịch sử mượn trả</p>
                  <p class="text-xs text-slate-500">Xem nhật ký mượn trả thiết bị</p>
                </div>
                <svg class="size-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </router-link>

              <!-- Link to Home -->
              <router-link
                to="/"
                class="flex items-center gap-3.5 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm transition hover:border-brand hover:shadow-md active:scale-[0.98]"
              >
                <div class="flex size-11 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-brand">
                  <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-bold text-ink">Mượn trả thiết bị</p>
                  <p class="text-xs text-slate-500">Mượn và trả thiết bị phòng học</p>
                </div>
                <svg class="size-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </router-link>

              <!-- Link to Admin (Conditional) -->
              <router-link
                v-if="isAdmin"
                to="/admin"
                class="flex items-center gap-3.5 rounded-2xl border border-blue-100 bg-white p-4 shadow-sm transition hover:border-brand hover:shadow-md active:scale-[0.98] sm:col-span-2"
              >
                <div class="flex size-11 shrink-0 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
                  <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-bold text-ink">Trang quản trị</p>
                  <p class="text-xs text-slate-500">Chức năng dành cho quản trị viên</p>
                </div>
                <svg class="size-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </router-link>
            </div>
          </div>

          <!-- Danger / Session Zone -->
          <div class="border-t border-blue-100 pt-6">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-2xl border border-red-100 bg-red-50/40 p-5">
              <div>
                <p class="text-sm font-bold text-red-900">Phiên làm việc trên thiết bị này</p>
                <p class="text-xs text-slate-500 mt-0.5">Xóa phiên đăng nhập hiện tại và quay về màn hình đăng nhập.</p>
              </div>
              <button
                @click="confirmLogout"
                class="inline-flex items-center justify-center gap-2 rounded-xl border border-red-200 bg-white px-5 py-2.5 text-xs sm:text-sm font-bold text-red-600 shadow-sm transition hover:bg-red-600 hover:text-white active:scale-[0.98] shrink-0"
              >
                <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                <span>Đăng xuất tài khoản</span>
              </button>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- Logout Confirmation Modal -->
    <div
      v-if="showLogoutModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm"
      @click.self="cancelLogout"
    >
      <div class="w-full max-w-sm rounded-3xl border border-blue-100 bg-white p-6 shadow-2xl animate-in fade-in zoom-in-95">
        <div class="flex size-12 items-center justify-center rounded-2xl bg-red-50 text-red-600 mb-4">
          <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </div>
        <h3 class="text-lg font-black text-slate-800">Xác nhận đăng xuất?</h3>
        <p class="mt-1 text-xs sm:text-sm text-slate-500">Bạn sẽ cần đăng nhập lại với mã tài khoản và mật khẩu để tiếp tục sử dụng hệ thống.</p>

        <div class="mt-6 flex items-center gap-3">
          <button
            @click="cancelLogout"
            class="flex-1 rounded-xl border border-slate-200 bg-white py-2.5 text-xs sm:text-sm font-bold text-slate-600 hover:bg-slate-50 transition active:scale-[0.98]"
          >
            Hủy bỏ
          </button>
          <button
            @click="logout"
            class="flex-1 rounded-xl bg-red-600 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md shadow-red-600/20 hover:bg-red-700 transition active:scale-[0.98]"
          >
            Đăng xuất
          </button>
        </div>
      </div>
    </div>

    <BottomNav :currentPath="currentPath" :is-admin="isAdmin" />
  </main>
</template>
