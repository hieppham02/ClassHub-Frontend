<script setup>
defineProps({
  currentPath: { type: String, default: '/' },
  isAdmin: { type: Boolean, default: false }
})
</script>

<template>
  <nav class="fixed bottom-0 left-0 right-0 z-45 flex h-16 items-center justify-around border-t border-blue-100 bg-white sm:hidden pb-safe">
    <a href="/" :class="currentPath === '/' ? 'text-brand font-bold' : 'text-slate-400 font-medium'" class="flex flex-col items-center gap-1 transition">
      <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
      <span class="text-[10px]">Trang chủ</span>
    </a>
    <a href="/history" :class="currentPath.includes('/history') ? 'text-brand font-bold' : 'text-slate-400 font-medium'" class="flex flex-col items-center gap-1 transition">
      <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      <span class="text-[10px]">Lịch sử</span>
    </a>
    <a v-if="isAdmin" href="/admin" :class="currentPath.startsWith('/admin') ? 'text-brand font-bold' : 'text-slate-400 font-medium'" class="flex flex-col items-center gap-1 transition">
      <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3l7 4v5c0 4.5-2.8 7.7-7 9-4.2-1.3-7-4.5-7-9V7l7-4z" /><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4" /></svg>
      <span class="text-[10px]">Quản trị</span>
    </a>
    <a href="/info" :class="currentPath.includes('/info') ? 'text-brand font-bold' : 'text-slate-400 font-medium'" class="flex flex-col items-center gap-1 transition">
      <svg class="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
      <span class="text-[10px]">Tài khoản</span>
    </a>
  </nav>
</template>
