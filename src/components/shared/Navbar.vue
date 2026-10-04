<script setup>
defineProps({
  user: { type: Object, default: () => ({ name: '', role: '' }) },
  currentPath: { type: String, default: '/' }
})
const emit = defineEmits(['logout'])
</script>

<template>
  <header class="border-b border-blue-100 bg-white/90 backdrop-blur sticky top-0 z-40">
    <div class="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
      <a href="/" class="flex items-center gap-3">
        <div class="flex size-11 items-center justify-center rounded-2xl bg-blue-50 ring-1 ring-blue-100">
          <img src="https://eaut.edu.vn/favicon.ico" class="size-8 object-contain" alt="Logo" />
        </div>
        <div>
          <p class="font-bold text-brand">Class Hub</p>
          <p class="text-xs text-slate-500">Đại học Công nghệ Đông Á</p>
        </div>
      </a>
      <nav class="hidden items-center gap-1 rounded-xl bg-blue-50 p-1 sm:flex">
        <a href="/" :class="currentPath === '/' ? 'bg-white font-bold text-brand shadow-sm' : 'font-medium text-slate-500 hover:text-brand'" class="rounded-lg px-4 py-2 text-sm transition">Trang chủ</a>
        <a href="/history" :class="currentPath.includes('/history') ? 'bg-white font-bold text-brand shadow-sm' : 'font-medium text-slate-500 hover:text-brand'" class="rounded-lg px-4 py-2 text-sm transition">Lịch sử mượn</a>
        <a
          v-if="user.role === 'ADMIN'"
          href="/admin"
          :class="currentPath.startsWith('/admin') ? 'bg-white font-bold text-brand shadow-sm' : 'font-medium text-slate-500 hover:text-brand'"
          class="rounded-lg px-4 py-2 text-sm transition"
        >
          Quản trị
        </a>
      </nav>
      <div class="hidden items-center gap-3 sm:flex">
        <a href="/info" class="text-right hover:opacity-80">
          <p class="text-sm font-semibold text-ink">{{ user.name }}</p>
          <p class="text-xs text-slate-500">{{ user.role }}</p>
        </a>
        <button @click="emit('logout')" class="rounded-lg border border-blue-100 px-3 py-2 text-xs font-bold text-brand hover:bg-blue-50">Đăng xuất</button>
      </div>
    </div>
  </header>
</template>
