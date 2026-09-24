<script setup>
import { useRoute } from 'vue-router'

const props = defineProps({
  currentPath: { type: String, default: '/admin' },
  adminName: { type: String, default: '' }
})
const emit = defineEmits(['logout'])
const route = useRoute()

const menuItems = [
  {
    label: 'Tổng quan',
    href: '/admin',
    exact: true,
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />`
  },
  {
    label: 'Quản lý tủ đồ',
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
    href: '/admin/history',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />`
  },
  {
    label: 'Trang người dùng',
    mobileLabel: 'Trang chủ',
    href: '/',
    exact: true,
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h5m4-4l4-4m0 0l-4-4m4 4H8" />`
  }
]

function isActive(item) {
  const path = route ? route.path : window.location.pathname
  if (item.exact) return path === item.href
  return path.startsWith(item.href)
}
</script>

<template>
  <aside class="hidden sm:flex flex-col w-60 shrink-0 h-screen sticky top-0 bg-white border-r border-blue-100 overflow-y-auto">
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

    <!-- Menu -->
    <nav class="flex flex-col gap-1 p-3 flex-1">
      <p class="px-3 pt-2 pb-1 text-[10px] font-bold uppercase tracking-widest text-slate-400">Menu chính</p>
      <router-link
        v-for="item in menuItems"
        :key="item.href"
        :to="item.href"
        :class="isActive(item)
          ? 'bg-brand text-white shadow-md shadow-brand/30'
          : 'text-slate-600 hover:bg-blue-50 hover:text-brand'"
        class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all"
      >
        <svg class="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" v-html="item.icon"></svg>
        {{ item.label }}
      </router-link>
    </nav>

    <!-- Admin info + logout -->
    <div class="border-b border-blue-50 p-3 shrink-0">
      <div class="mb-2 px-3 py-2 rounded-xl bg-blue-50">
        <p class="text-xs font-bold text-ink truncate">{{ adminName || 'Admin' }}</p>
        <p class="text-[10px] text-slate-400 mt-0.5">Quản trị viên</p>
      </div>
      <button
        @click="emit('logout')"
        class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-red-500 hover:bg-red-50 transition-all"
      >
        <svg class="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        Đăng xuất
      </button>
    </div>
  </aside>
  
  <nav class="sm:hidden fixed bottom-0 left-0 right-0 z-40 flex h-16 items-center justify-around border-t border-blue-100 bg-white pb-safe">
    <router-link
      v-for="item in menuItems"
      :key="item.href"
      :to="item.href"
      :class="isActive(item) ? 'text-brand' : 'text-slate-400'"
      class="flex flex-col items-center gap-0.5 flex-1 transition"
    >
      <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" v-html="item.icon"></svg>
      <span class="text-[9px] font-semibold leading-none truncate max-w-[52px] text-center">{{ item.mobileLabel || item.label }}</span>
    </router-link>
  </nav>
</template>
