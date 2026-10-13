<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  currentPath: { type: String, default: '/admin' },
  adminName: { type: String, default: '' }
})
const emit = defineEmits(['logout'])
const route = useRoute()

const showMobileDrawer = ref(false)

const menuItems = [
  {
    label: 'Tổng quan',
    href: '/admin',
    exact: true,
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />`
  },
  {
    label: 'Quản lý tủ đồ',
    mobileLabel: 'Tủ đồ',
    href: '/admin/cabinets',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />`
  },
  {
    label: 'Tài khoản',
    href: '/admin/accounts',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />`
  },
  {
    label: 'Tòa nhà & Phòng',
    href: '/admin/buildings',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />`
  },
  {
    label: 'Lịch sử mượn trả',
    mobileLabel: 'Lịch sử',
    href: '/admin/history',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />`
  },
  {
    label: 'Thống kê',
    href: '/admin/statistics',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />`
  },
  {
    label: 'Quản lý tài sản',
    href: '/admin/assets',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M4 7l8-4 8 4v10l-8 4-8-4V7zm0 0l8 4 8-4m-8 4v10" />`
  },
  {
    label: 'Trang người dùng',
    mobileLabel: 'Trang chủ',
    href: '/',
    exact: true,
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h5m4-4l4-4m0 0l-4-4m4 4H8" />`
  }
]

// 3 mục chính trên bottom bar
const primaryMobileTabs = [
  menuItems[0], // Tổng quan
  menuItems[1], // Quản lý tủ
  menuItems[4]  // Lịch sử
]

// Các mục phụ trong Drawer "Thêm"
const secondaryMobileTabs = [
  menuItems[6], // Quản lý tài sản
  menuItems[2], // Tài khoản
  menuItems[3], // Tòa nhà & Phòng
  menuItems[5], // Thống kê
  menuItems[7]  // Trang người dùng
]

function isActive(item) {
  const path = route ? route.path : window.location.pathname
  if (item.exact) return path === item.href
  return path.startsWith(item.href)
}

const isMoreActive = computed(() => {
  return secondaryMobileTabs.some(item => isActive(item))
})
</script>

<template>
  <!-- Desktop Sidebar -->
  <aside class="hidden sm:flex flex-col w-60 shrink-0 h-[100dvh] sticky top-0 bg-white border-r border-blue-100 overflow-y-auto">
    <!-- Logo -->
    <div class="flex items-center gap-3 px-5 py-5 border-b border-blue-50 shrink-0">
      <div class="flex size-10 items-center justify-center rounded-2xl bg-blue-50 ring-1 ring-blue-100 shrink-0">
        <img src="https://eaut.edu.vn/favicon.ico" class="size-7 object-contain" alt="Logo" />
      </div>
      <div class="min-w-0">
        <p class="font-bold text-brand text-sm leading-tight">Class Hub</p>
        <p class="text-[11px] text-slate-400 truncate">Quản trị hệ thống</p>
      </div>
    </div>

    <!-- Menu Desktop -->
    <nav class="flex flex-col gap-1 p-3 flex-1">
      <p class="px-3 pt-2 pb-1 text-[10px] font-bold uppercase tracking-widest text-slate-400">Menu chính</p>
      <router-link
        v-for="item in menuItems"
        :key="item.href"
        :to="item.href"
        :class="isActive(item)
          ? 'bg-brand text-white shadow-md shadow-brand/30'
          : 'text-slate-600 hover:bg-blue-50 hover:text-brand'"
        class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold active:scale-[0.98] transition-all"
      >
        <svg class="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" v-html="item.icon"></svg>
        {{ item.label }}
      </router-link>
    </nav>

    <!-- Admin info + logout Desktop -->
    <div class="border-t border-blue-100 p-3 shrink-0">
      <div class="mb-2 px-3 py-2 rounded-xl bg-blue-50">
        <p class="text-xs font-bold text-ink truncate">{{ adminName || 'Admin' }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Quản trị viên</p>
      </div>
      <button
        @click="emit('logout')"
        class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-red-500 hover:bg-red-50 active:scale-[0.98] transition-all"
      >
        <svg class="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        Đăng xuất
      </button>
    </div>
  </aside>
  
  <!-- Mobile Bottom Navigation (Tối ưu 4 nút chuẩn touch target >= 48px) -->
  <nav class="sm:hidden fixed bottom-0 left-0 right-0 z-40 flex h-16 items-center justify-around border-t border-blue-100 bg-white/95 backdrop-blur-sm pb-safe">
    <router-link
      v-for="item in primaryMobileTabs"
      :key="item.href"
      :to="item.href"
      :class="isActive(item) ? 'text-brand font-bold' : 'text-slate-400 font-medium'"
      class="flex flex-col items-center justify-center flex-1 h-full gap-1 active:scale-95 transition"
    >
      <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" v-html="item.icon"></svg>
      <span class="text-[10px] leading-none">{{ item.mobileLabel || item.label }}</span>
    </router-link>

    <!-- Nút "Thêm" mở Drawer -->
    <button
      @click="showMobileDrawer = true"
      :class="isMoreActive ? 'text-brand font-bold' : 'text-slate-400 font-medium'"
      class="flex flex-col items-center justify-center flex-1 h-full gap-1 active:scale-95 transition"
    >
      <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
        <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
      <span class="text-[10px] leading-none">Thêm</span>
    </button>
  </nav>

  <!-- Mobile Action Drawer (Bottom Sheet) -->
  <div
    v-if="showMobileDrawer"
    class="sm:hidden fixed inset-0 z-50 flex flex-col justify-end bg-slate-900/40 backdrop-blur-xs"
    @click.self="showMobileDrawer = false"
  >
    <div class="rounded-t-3xl border-t border-blue-100 bg-white p-5 shadow-2xl animate-fadeIn">
      <div class="mx-auto mb-3 h-1 w-10 rounded-full bg-slate-200"></div>
      
      <div class="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <h3 class="text-sm font-bold text-slate-800">Menu quản trị mở rộng</h3>
          <p class="text-[11px] text-slate-400">{{ adminName || 'Quản trị viên' }}</p>
        </div>
        <button
          @click="showMobileDrawer = false"
          class="flex size-8 items-center justify-center rounded-full bg-slate-100 text-slate-500 active:scale-95 transition"
        >
          <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Danh sách tab phụ -->
      <div class="my-3 flex flex-col gap-1.5">
        <router-link
          v-for="item in secondaryMobileTabs"
          :key="item.href"
          :to="item.href"
          @click="showMobileDrawer = false"
          :class="isActive(item)
            ? 'bg-blue-50 text-brand font-bold border border-blue-200'
            : 'text-slate-700 hover:bg-slate-50 font-medium'"
          class="flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm active:scale-[0.98] transition"
        >
          <svg class="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" v-html="item.icon"></svg>
          <span>{{ item.label }}</span>
        </router-link>
      </div>

      <!-- Đăng xuất trong drawer -->
      <button
        @click="emit('logout'); showMobileDrawer = false"
        class="mt-2 flex w-full items-center justify-center gap-2 rounded-xl border border-red-100 bg-red-50/60 py-3 text-xs font-bold text-red-600 active:scale-[0.98] transition"
      >
        <svg class="size-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        Đăng xuất khỏi hệ thống
      </button>
    </div>
  </div>
</template>
