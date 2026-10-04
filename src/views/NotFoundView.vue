<script setup>
import { computed } from 'vue'
import { hasRole, isAuthenticated } from '@/services/authSession.js'

const homePath = computed(() => hasRole('ADMIN') ? '/admin' : '/')
const homeLabel = computed(() => isAuthenticated() ? 'Về trang chính' : 'Đến trang đăng nhập')
const destination = computed(() => isAuthenticated() ? homePath.value : '/login')
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-mist px-5 text-center">
    <section class="max-w-lg">
      <p class="text-sm font-bold uppercase text-brand">Lỗi 404</p>
      <h1 class="mt-3 text-3xl font-black text-ink sm:text-4xl">Không tìm thấy trang</h1>
      <p class="mt-3 text-sm leading-6 text-slate-500">
        Đường dẫn này không tồn tại hoặc đã được thay đổi.
      </p>
      <RouterLink
        :to="destination"
        class="mt-7 inline-flex h-11 items-center justify-center rounded-lg bg-brand px-5 text-sm font-bold text-white transition hover:bg-brand-dark"
      >
        {{ homeLabel }}
      </RouterLink>
    </section>
  </main>
</template>
