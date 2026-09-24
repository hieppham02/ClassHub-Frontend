<script setup>
import { ref, onMounted } from 'vue'
import Navbar from '@/components/Navbar.vue'
import BottomNav from '@/components/BottomNav.vue'

const user = ref({ name: '', role: '', email: '' })
const currentPath = ref(window.location.pathname)

onMounted(() => {
  const saved = sessionStorage.getItem('classhub-user')
  if (saved) {
    user.value = JSON.parse(saved)
    if (user.value.role === "SINHVIEN") user.value.role = "Sinh viên"
    if (user.value.role === "GIANGVIEN") user.value.role = "Giảng viên"
  } else {
    window.location.href = '/login'
  }
})

function logout() {
  sessionStorage.removeItem('classhub-token')
  sessionStorage.removeItem('classhub-user')
  window.location.href = '/login'
}
</script>

<template>
  <main class="min-h-screen bg-mist pb-20 sm:pb-0">
    <Navbar :user="user" :currentPath="currentPath" @logout="logout" />

    <section class="mx-auto max-w-3xl px-5 py-12 lg:px-8">
      <p class="text-sm font-bold uppercase tracking-[0.18em] text-brand">TÀI KHOẢN</p>
      <h1 class="mt-2 text-4xl font-bold text-ink">Thông tin người dùng</h1>
      <div class="mt-8 overflow-hidden rounded-3xl border border-blue-100 bg-white shadow-lg">
        <div class="bg-gradient-to-r from-brand-dark to-brand p-8 text-white">
          <div class="flex size-20 items-center justify-center rounded-3xl bg-white/15 text-3xl font-bold ring-1 ring-white/30">{{ user.name.charAt(0) }}</div>
          <h2 class="mt-5 text-2xl font-bold">{{ user.name }}</h2>
          <p class="mt-1 text-blue-100">{{ user.role }}</p>
        </div>
        <div class="border-t border-blue-100 p-8">
          <button @click="logout" class="rounded-xl border border-red-100 px-4 py-3 text-sm font-bold text-red-600 hover:bg-red-50">Đăng xuất tài khoản</button>
        </div>
      </div>
    </section>

    <BottomNav :currentPath="currentPath" :is-admin="user.role === 'ADMIN'" />
  </main>
</template>
