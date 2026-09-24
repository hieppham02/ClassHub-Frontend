<script setup>
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import { ref, reactive, onMounted } from 'vue'
import { api } from '@/services/apiClient.js'

const activeTab = ref('buildings')
const isLoading = ref(false)
const showModal = ref(false)
const isEditing = ref(false)

const buildings = ref([])
const rooms = ref([])

// Form Tòa nhà
const buildingForm = reactive({
  id: '',
  name: '',
  floors: 5,
  description: ''
})

// Form Phòng học
const roomForm = reactive({
  id: '',
  name: '',
  buildingId: '',
  floor: 1,
  capacity: 70,
  status: 'HOAT_DONG'
})

// 1. Tải danh sách Tòa nhà & Phòng học từ API
async function fetchData() {
  isLoading.value = true

  try {
    const [buildingsResult, roomsResult] = await Promise.allSettled([
      api.get('/admin/buildings'),
      api.get('/admin/rooms')
    ])

    if (buildingsResult.status === 'fulfilled') buildings.value = buildingsResult.value
    if (roomsResult.status === 'fulfilled') rooms.value = roomsResult.value

    const failedRequest = [buildingsResult, roomsResult]
      .find((result) => result.status === 'rejected')
    if (failedRequest) throw failedRequest.reason
  } catch (err) {
    console.error('Lỗi khi tải dữ liệu:', err)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchData()
})

// 2. Mở Modal Thêm mới / Sửa
function openAddModal() {
  isEditing.value = false
  if (activeTab.value === 'buildings') {
    Object.assign(buildingForm, { id: '', name: '', floors: 5, description: '' })
  } else {
    Object.assign(roomForm, {
      id: '',
      name: '',
      buildingId: buildings.value[0]?.id || '',
      floor: 1,
      capacity: 70,
      status: 'HOAT_DONG'
    })
  }
  showModal.value = true
}

function openEditBuilding(b) {
  isEditing.value = true
  Object.assign(buildingForm, {
    id: b.id,
    name: b.name,
    floors: b.floors,
    description: b.description
  })
  showModal.value = true
}

function openEditRoom(r) {
  isEditing.value = true
  Object.assign(roomForm, {
    id: r.id,
    name: r.name,
    buildingId: r.buildingId,
    floor: r.floorNum,
    capacity: r.capacity,
    status: r.rawStatus
  })
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

// 3. Lưu Tòa nhà (Thêm / Sửa)
async function saveBuilding() {
  if (!buildingForm.id || !buildingForm.name) return alert('Vui lòng nhập đủ thông tin!')

  const endpoint = isEditing.value
    ? `/admin/buildings/${buildingForm.id}`
    : '/admin/buildings'

  try {
    const data = isEditing.value
      ? await api.put(endpoint, buildingForm)
      : await api.post(endpoint, buildingForm)
    alert(data?.message || 'Thành công!')
    closeModal()
    fetchData()
  } catch (err) {
    alert(err.message || 'Lỗi kết nối máy chủ!')
  }
}

// 4. Lưu Phòng học (Thêm / Sửa)
async function saveRoom() {
  if (!roomForm.id || !roomForm.name || !roomForm.buildingId) return alert('Vui lòng nhập đủ thông tin phòng!')

  const endpoint = isEditing.value
    ? `/admin/rooms/${roomForm.id}`
    : '/admin/rooms'

  try {
    const data = isEditing.value
      ? await api.put(endpoint, roomForm)
      : await api.post(endpoint, roomForm)
    alert(data?.message || 'Thành công!')
    closeModal()
    fetchData()
  } catch (err) {
    alert(err.message || 'Lỗi kết nối máy chủ!')
  }
}

// 5. Xóa Tòa nhà / Phòng học
async function deleteItem(type, id, name) {
  if (!confirm(`Bạn có chắc chắn muốn xóa ${type === 'b' ? 'Tòa nhà' : 'Phòng học'}: ${name} (${id})?`)) return

  const endpoint = type === 'b' ? `/admin/buildings/${id}` : `/admin/rooms/${id}`

  try {
    const data = await api.delete(endpoint)
    alert(data?.message || 'Đã xóa thành công!')
    fetchData()
  } catch (err) {
    alert(err.message || 'Lỗi kết nối máy chủ!')
  }
}
</script>

<template>
  <AdminLayout>
    <div class="w-full">
      <!-- Header NEO CỐ ĐỊNH -->
      <div class="sticky top-0 z-40 bg-mist/95 backdrop-blur-sm border-b border-slate-200/60 shadow-sm px-4 sm:px-6 lg:px-32 pt-6 pb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-widest text-slate-400">Cơ sở hạ tầng</p>
          <h1 class="mt-0.5 text-2xl font-black text-ink">Tòa nhà &amp; Phòng học</h1>
        </div>
        <div class="flex items-center gap-3">
          <button 
            @click="fetchData" 
            :disabled="isLoading"
            class="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 h-10 text-xs font-bold text-slate-600 hover:bg-slate-50 transition shadow-sm"
          >
            <span :class="{ 'animate-spin': isLoading }"><font-awesome-icon icon="fa-solid fa-arrows-rotate" class="size-4 text-slate-500" /></span>
            <span> Làm mới</span>
          </button>
          <button 
            @click="openAddModal" 
            class="h-10 rounded-xl bg-brand px-5 text-sm font-bold text-white shadow-md shadow-brand/20 hover:bg-brand-dark transition shrink-0"
          >
            + Thêm {{ activeTab === 'buildings' ? 'Tòa nhà' : 'Phòng học' }}
          </button>
        </div>
      </div>

      <!-- Nội dung Body -->
      <div class="px-4 sm:px-6 lg:px-32 pt-5 pb-10">
        
        <!-- Tabs -->
        <div class="mb-5 flex gap-1 rounded-xl bg-blue-50 p-1 w-fit shadow-sm">
          <button 
            @click="activeTab = 'buildings'" 
            :class="activeTab === 'buildings' ? 'bg-white text-brand font-bold shadow-sm' : 'text-slate-500 font-medium hover:text-brand'" 
            class="rounded-lg px-6 py-2 text-sm transition"
          >
            Tòa nhà ({{ buildings.length }})
          </button>
          <button 
            @click="activeTab = 'rooms'" 
            :class="activeTab === 'rooms' ? 'bg-white text-brand font-bold shadow-sm' : 'text-slate-500 font-medium hover:text-brand'" 
            class="rounded-lg px-6 py-2 text-sm transition"
          >
            Phòng học ({{ rooms.length }})
          </button>
        </div>

        <!-- ================= TAB 1: TÒA NHÀ ================= -->
        <div v-if="activeTab === 'buildings'" class="rounded-2xl border border-blue-100 bg-white shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-blue-50 bg-blue-50/60">
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Mã tòa</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Tên tòa nhà</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Số tầng</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Số phòng trực thuộc</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Ghi chú</th>
                  <th class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in buildings" :key="b.id" class="border-b border-blue-50 transition hover:bg-blue-50/30">
                  <td class="px-5 py-4 font-bold text-slate-800 whitespace-nowrap">{{ b.id }}</td>
                  <td class="px-5 py-4 font-semibold text-ink whitespace-nowrap">{{ b.name }}</td>
                  <td class="px-5 py-4 font-medium text-slate-600 whitespace-nowrap">{{ b.floors }} tầng</td>
                  <td class="px-5 py-4 whitespace-nowrap">
                    <span class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-brand border border-blue-100">
                      {{ b.rooms }} phòng
                    </span>
                  </td>
                  <td class="px-5 py-4 text-slate-500 text-xs whitespace-nowrap">{{ b.description || '---' }}</td>
                  <td class="px-5 py-4 text-center whitespace-nowrap">
                    <div class="flex items-center justify-center gap-3">
                      <button @click="openEditBuilding(b)" class="font-semibold text-brand hover:text-brand-dark transition">Sửa</button>
                      <button @click="deleteItem('b', b.id, b.name)" class="font-semibold text-red-500 hover:text-red-700 transition">Xóa</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ================= TAB 2: PHÒNG HỌC ================= -->
        <div v-if="activeTab === 'rooms'" class="rounded-2xl border border-blue-100 bg-white shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-blue-50 bg-blue-50/60">
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Mã phòng</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Tên phòng</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Tòa nhà</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Tầng</th>
                  <th class="px-5 py-4 text-left text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Sức chứa</th>
                  <th class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Trạng thái</th>
                  <th class="px-5 py-4 text-center text-xs font-bold uppercase tracking-wide text-slate-500 whitespace-nowrap">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in rooms" :key="r.id" class="border-b border-blue-50 transition hover:bg-blue-50/30">
                  <td class="px-5 py-4 font-bold text-slate-800 whitespace-nowrap">{{ r.id }}</td>
                  <td class="px-5 py-4 font-semibold text-ink whitespace-nowrap">{{ r.name }}</td>
                  <td class="px-5 py-4 font-medium text-slate-600 whitespace-nowrap">{{ r.building }}</td>
                  <td class="px-5 py-4 font-medium text-slate-600 whitespace-nowrap">{{ r.floor }}</td>
                  <td class="px-5 py-4 text-slate-600 whitespace-nowrap">{{ r.capacity }} chỗ</td>
                  <td class="px-5 py-4 text-center whitespace-nowrap">
                    <span 
                      :class="{
                        'bg-emerald-100 text-emerald-700': r.status === 'Sẵn sàng', 
                        'bg-amber-100 text-amber-700': r.status === 'Đang mượn', 
                        'bg-red-100 text-red-700': r.status === 'Bảo trì' || r.status === 'Tạm khóa'
                      }" 
                      class="rounded-md px-2.5 py-1 text-xs font-bold"
                    >
                      {{ r.status }}
                    </span>
                  </td>
                  <td class="px-5 py-4 text-center whitespace-nowrap">
                    <div class="flex items-center justify-center gap-3">
                      <button @click="openEditRoom(r)" class="font-semibold text-brand hover:text-brand-dark transition">Sửa</button>
                      <button @click="deleteItem('r', r.id, r.name)" class="font-semibold text-red-500 hover:text-red-700 transition">Xóa</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

      <!-- ================= MODAL THÊM / SỬA ================= -->
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
        <div class="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
          
          <!-- Modal Header -->
          <div class="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
            <h3 class="text-lg font-bold text-ink">
              {{ isEditing ? 'Chỉnh sửa' : 'Thêm mới' }} {{ activeTab === 'buildings' ? 'Tòa nhà' : 'Phòng học' }}
            </h3>
            <button @click="closeModal" class="text-slate-400 hover:text-slate-600 font-bold text-xl">✕</button>
          </div>

          <!-- FORM TÒA NHÀ -->
          <form v-if="activeTab === 'buildings'" class="space-y-4" @submit.prevent="saveBuilding">
            <div>
              <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Mã tòa nhà</label>
              <input 
                v-model="buildingForm.id" 
                :disabled="isEditing"
                type="text" 
                required 
                placeholder="VD: DTD, EAUT, PLC"
                class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand disabled:opacity-60 uppercase"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Tên tòa nhà</label>
              <input 
                v-model="buildingForm.name" 
                type="text" 
                required 
                placeholder="VD: Tòa nhà Đinh Trọng Dật"
                class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Số tầng</label>
              <input 
                v-model.number="buildingForm.floors" 
                type="number" 
                min="1" 
                max="50" 
                required 
                class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
              />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Mô tả / Ghi chú</label>
              <input 
                v-model="buildingForm.description" 
                type="text" 
                placeholder="VD: Khu thực hành CNTT"
                class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
              />
            </div>

            <div class="mt-6 flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button type="button" @click="closeModal" class="h-10 rounded-xl bg-slate-100 px-4 text-xs font-bold text-slate-600">Hủy</button>
              <button type="submit" class="h-10 rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-md shadow-brand/20 hover:bg-brand-dark">Lưu</button>
            </div>
          </form>

          <!-- FORM PHÒNG HỌC -->
          <form v-else class="space-y-4" @submit.prevent="saveRoom">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Mã phòng</label>
                <input 
                  v-model="roomForm.id" 
                  :disabled="isEditing"
                  type="text" 
                  required 
                  placeholder="VD: DTD201"
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand disabled:opacity-60 uppercase"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Tên hiển thị</label>
                <input 
                  v-model="roomForm.name" 
                  type="text" 
                  required 
                  placeholder="VD: DTD-201"
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Thuộc Tòa nhà</label>
                <select v-model="roomForm.buildingId" required class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand">
                  <option v-for="b in buildings" :key="b.id" :value="b.id">{{ b.name }} ({{ b.id }})</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Tầng số</label>
                <input 
                  v-model.number="roomForm.floor" 
                  type="number" 
                  min="1" 
                  max="30" 
                  required 
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Sức chứa (Chỗ)</label>
                <input 
                  v-model.number="roomForm.capacity" 
                  type="number" 
                  min="10" 
                  max="500" 
                  required 
                  class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand"
                />
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 uppercase mb-1">Trạng thái phòng</label>
                <select v-model="roomForm.status" class="h-10 w-full rounded-xl border border-blue-100 bg-mist px-3 text-sm outline-none focus:ring-2 focus:ring-brand">
                  <option value="HOAT_DONG">Sẵn sàng (Hoạt động)</option>
                  <option value="BAO_TRI">Bảo trì</option>
                  <option value="TAM_KHOA">Tạm khóa</option>
                </select>
              </div>
            </div>

            <div class="mt-6 flex justify-end gap-3 pt-3 border-t border-slate-100">
              <button type="button" @click="closeModal" class="h-10 rounded-xl bg-slate-100 px-4 text-xs font-bold text-slate-600">Hủy</button>
              <button type="submit" class="h-10 rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-md shadow-brand/20 hover:bg-brand-dark">Lưu</button>
            </div>
          </form>

        </div>
      </div>

    </div>
  </AdminLayout>
</template>
