<script setup>
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import { ref, computed, reactive, onMounted } from 'vue'
import { api } from '@/services/apiClient.js'

const search = ref('')
const roleFilter = ref('Tất cả')
const statusFilter = ref('Tất cả')
const isLoading = ref(false)

const showModal = ref(false)
const isEditing = ref(false)

const accountForm = reactive({
  id: '',
  name: '',
  role: 'Sinh viên',
  classOrDept: '',
  email: '',
  phone: '',
  password: ''
})

const accounts = ref([])

async function fetchAccounts() {
  isLoading.value = true

  try {
    accounts.value = await api.get('/admin/accounts')
  } catch (err) {
    console.error('Lỗi tải danh sách tài khoản:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchAccounts()
})

const filteredAccounts = computed(() => {
  return accounts.value.filter(acc => {
    const matchRole = roleFilter.value === 'Tất cả' || acc.role === roleFilter.value
    const matchStatus = statusFilter.value === 'Tất cả'
      || (statusFilter.value === 'Hoạt động' && acc.isActive)
      || (statusFilter.value === 'Bị khóa' && !acc.isActive)

    const keyword = search.value.toLowerCase().trim()
    const matchSearch = !keyword
      || acc.name.toLowerCase().includes(keyword)
      || acc.id.toLowerCase().includes(keyword)
      || acc.email.toLowerCase().includes(keyword)
      || acc.className.toLowerCase().includes(keyword)

    return matchRole && matchStatus && matchSearch
  })
})

function openAddModal() {
  isEditing.value = false
  Object.assign(accountForm, { id: '', name: '', role: 'Sinh viên', classOrDept: '', email: '', phone: '', password: '' })
  showModal.value = true
}

function openEditModal(acc) {
  isEditing.value = true
  Object.assign(accountForm, {
    id: acc.id,
    name: acc.name,
    role: acc.role,
    classOrDept: acc.className === '---' ? '' : acc.className,
    email: acc.email,
    phone: acc.phone === '---' ? '' : acc.phone,
    password: ''
  })
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function saveAccount() {
  if (!accountForm.id || !accountForm.name || !accountForm.email) {
    return alert('Vui lòng nhập đầy đủ Mã, Họ tên và Email!')
  }

  const endpoint = isEditing.value
    ? `/admin/accounts/${accountForm.id}`
    : '/admin/accounts'
  const payload = isEditing.value ? {
    name: accountForm.name,
    email: accountForm.email,
    phone: accountForm.phone,
    role: accountForm.role,
    classOrDept: accountForm.classOrDept,
    newPassword: accountForm.password || null
  } : {
    id: accountForm.id,
    name: accountForm.name,
    email: accountForm.email,
    phone: accountForm.phone,
    role: accountForm.role,
    classOrDept: accountForm.classOrDept,
    password: accountForm.password || '123456'
  }

  try {
    const data = isEditing.value
      ? await api.put(endpoint, payload)
      : await api.post(endpoint, payload)
    alert(data?.message || 'Thành công!')
    closeModal()
    fetchAccounts()
  } catch (err) {
    alert(err.message || 'Lỗi kết nối máy chủ!')
  }
}

async function toggleStatus(acc) {
  const actionText = acc.isActive ? 'KHÓA' : 'MỞ KHÓA'
  if (!confirm(`Bạn có chắc muốn ${actionText} tài khoản: ${acc.name} (${acc.id})?`)) return

  try {
    const data = await api.patch(`/admin/accounts/${acc.id}/toggle-status`)
    acc.isActive = data.isActive
  } catch (err) {
    alert(err.message || 'Lỗi kết nối máy chủ!')
  }
}

async function deleteAccount(acc) {
  if (!confirm(`CẢNH BÁO: Bạn có chắc chắn muốn XÓA VĨNH VIỄN tài khoản ${acc.name} (${acc.id})?`)) return

  try {
    const data = await api.delete(`/admin/accounts/${acc.id}`)
    alert(data?.message || 'Đã xóa!')
    fetchAccounts()
  } catch (err) {
    alert(err.message || 'Lỗi kết nối máy chủ!')
  }
}
</script>

<template>
  <AdminLayout>
    <div class="w-full">
      <!-- Header NEO CỐ ĐỊNH -->
      <div
        class="sticky top-0 z-40 bg-mist/95 backdrop-blur-sm border-b border-slate-200/60 shadow-sm px-4 sm:px-6 lg:px-32 pt-6 pb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-widest text-slate-400">Quản lý người dùng</p>
          <h1 class="mt-0.5 text-2xl font-black text-ink">Tài khoản hệ thống</h1>
        </div>
        <div class="flex items-center gap-3">
          <button @click="fetchAccounts" :disabled="isLoading"
            class="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 h-10 text-xs font-bold text-slate-600 hover:bg-slate-50 transition shadow-sm">
            <span :class="{ 'animate-spin': isLoading }"></span>
            <span><font-awesome-icon icon="fa-solid fa-arrows-rotate" class="size-4 text-slate-500" /> Làm mới</span>
          </button>
          <button @click="openAddModal"
            class="h-10 rounded-xl bg-brand px-5 text-sm font-bold text-white shadow-md shadow-brand/20 hover:bg-brand-dark transition shrink-0">
            + Thêm tài khoản
          </button>
        </div>
      </div>

      <!-- Nội dung Body -->
      <div class="px-4 sm:px-6 lg:px-32 pt-5 pb-10">

        <!-- Filter bar -->
        <div class="mb-5 flex flex-col sm:flex-row gap-3">
          <input v-model="search" type="text" placeholder="Tìm theo tên, mã SV/GV, email, lớp..."
            class="h-11 flex-1 rounded-xl border border-blue-100 bg-white px-4 text-sm outline-none focus:ring-2 focus:ring-brand shadow-sm" />

          <select v-model="roleFilter"
            class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-brand sm:w-40 shadow-sm">
            <option>Tất cả</option>
            <option>Sinh viên</option>
            <option>Giảng viên</option>
            <option>Admin</option>
          </select>

          <select v-model="statusFilter"
            class="h-11 rounded-xl border border-blue-100 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-brand sm:w-40 shadow-sm">
            <option>Tất cả</option>
            <option>Hoạt động</option>
            <option>Bị khóa</option>
          </select>
        </div>

        <!-- Table -->
        <div class="rounded-2xl border border-blue-100 bg-white shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-blue-50 bg-blue-50/60">
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Mã SV/User</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Họ và tên</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Vai trò</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Lớp / Đơn vị</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Email</th>
                  <th
                    class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    SĐT</th>
                  <th
                    class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Trạng thái</th>
                  <th
                    class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">
                    Thao tác</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="acc in filteredAccounts" :key="acc.id"
                  class="border-b border-blue-50 transition hover:bg-blue-50/30">
                  <td class="px-5 py-4 font-bold text-slate-800 whitespace-nowrap">{{ acc.id }}</td>
                  <td class="px-5 py-4 font-semibold text-ink whitespace-nowrap">{{ acc.name }}</td>
                  <td class="px-5 py-4 whitespace-nowrap">
                    <span :class="{
                      'bg-amber-100 text-amber-700': acc.role === 'Admin',
                      'bg-emerald-100 text-emerald-700': acc.role === 'Giảng viên',
                      'bg-blue-100 text-blue-700': acc.role === 'Sinh viên'
                    }" class="rounded-md px-2.5 py-1 text-xs font-bold">
                      {{ acc.role }}
                    </span>
                  </td>
                  <td class="px-5 py-4 text-slate-600 whitespace-nowrap">{{ acc.className }}</td>
                  <td class="px-5 py-4 text-slate-600 whitespace-nowrap">{{ acc.email }}</td>
                  <td class="px-5 py-4 text-slate-600 whitespace-nowrap">{{ acc.phone }}</td>

                  <!-- Trạng thái (Active / Locked) -->
                  <td class="px-5 py-4 text-center whitespace-nowrap">
                    <span
                      :class="acc.isActive ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-600 border-red-200'"
                      class="inline-flex items-center gap-1 rounded-md border px-2.5 py-0.5 text-xs font-bold">
                      <span>{{ acc.isActive ? '● Hoạt động' : '● Bị khóa' }}</span>
                    </span>
                  </td>

                  <!-- Thao tác -->
                  <td class="px-5 py-4 text-center whitespace-nowrap">
                    <div class="flex items-center justify-center gap-2">
                      <button @click="openEditModal(acc)"
                        class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-brand hover:bg-brand hover:text-white transition">
                        Sửa
                      </button>
                      <button @click="toggleStatus(acc)"
                        :class="acc.isActive ? 'text-amber-600 bg-amber-50 hover:bg-amber-600' : 'text-emerald-600 bg-emerald-50 hover:bg-emerald-600'"
                        class="rounded-lg px-2.5 py-1 text-xs font-bold hover:text-white transition">
                        {{ acc.isActive ? 'Khóa' : 'Mở' }}
                      </button>
                      <button @click="deleteAccount(acc)"
                        class="rounded-lg bg-red-50 px-2.5 py-1 text-xs font-bold text-red-600 hover:bg-red-600 hover:text-white transition">
                        Xóa
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="filteredAccounts.length === 0">
                  <td colspan="8" class="py-16 text-center text-slate-400">
                    {{ isLoading ? 'Đang tải dữ liệu...' : 'Không tìm thấy tài khoản nào.' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <!-- MODAL THÊM / SỬA TÀI KHOẢN -->
      <div v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
        <div class="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl">
          <div class="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
            <h3 class="text-lg font-bold text-ink">
              {{ isEditing ? 'Chỉnh sửa tài khoản' : 'Thêm mới tài khoản' }}
            </h3>
            <button @click="closeModal" class="text-slate-400 hover:text-slate-600 font-bold text-xl">✕</button>
          </div>

          <form class="space-y-3.5" @submit.prevent="saveAccount">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Mã SV/User</label>
                <input v-model="accountForm.id" :disabled="isEditing" type="text" required placeholder="VD: 20231206"
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand disabled:opacity-60" />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Vai trò</label>
                <select v-model="accountForm.role"
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand">
                  <option>Sinh viên</option>
                  <option>Giảng viên</option>
                  <option>Admin</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Họ và tên</label>
              <input v-model="accountForm.name" type="text" required placeholder="VD: Phạm Hoàng Hiệp"
                class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand" />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Email</label>
                <input v-model="accountForm.email" type="email" required placeholder="VD: 20231206@eaut.edu.vn"
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand" />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Số điện thoại</label>
                <input v-model="accountForm.phone" type="text" placeholder="VD: 0969299262"
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand" />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Lớp / Đơn vị</label>
                <input v-model="accountForm.classOrDept" type="text" placeholder="VD: DCCNTT.14.3"
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand" />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">
                  {{ isEditing ? 'Mật khẩu mới (Tùy chọn)' : 'Mật khẩu khởi tạo' }}
                </label>
                <input v-model="accountForm.password" type="password"
                  :placeholder="isEditing ? 'Để trống nếu giữ nguyên' : 'Mặc định: 123456'"
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand" />
              </div>
            </div>

            <div class="mt-6 flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button type="button" @click="closeModal"
                class="h-10 rounded-xl bg-slate-100 px-4 text-xs font-bold text-slate-600 hover:bg-slate-200 transition">
                Hủy bỏ
              </button>
              <button type="submit"
                class="h-10 rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-md shadow-brand/20 hover:bg-brand-dark transition">
                {{ isEditing ? 'Lưu thay đổi' : 'Tạo tài khoản' }}
              </button>
            </div>
          </form>
        </div>
      </div>

    </div>
  </AdminLayout>
</template>
