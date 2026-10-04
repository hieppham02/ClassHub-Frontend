<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/apiClient.js'

const router = useRouter()

const msv = ref('')
const mk = ref('')
const error = ref('')
const isLoading = ref(false)
const showPassword = ref(false)

async function login() {
  if (!msv.value.trim() || !mk.value) {
    error.value = 'Vui lòng nhập đầy đủ mã sinh viên và mật khẩu.'
    return
  }

  error.value = ''
  isLoading.value = true

  try {
    const data = await api.post('/auth/login', {
      maSv: msv.value.trim(),
      matKhau: mk.value
    }, { auth: false })

    if (!data?.token || !data?.user) {
      error.value = data.message || 'Đăng nhập thất bại! Vui lòng kiểm tra lại.'
      isLoading.value = false
      return
    }

    sessionStorage.setItem('classhub-token', data.token)
    sessionStorage.setItem('classhub-user', JSON.stringify(data.user))

    const userRole = data.user.role
    if (userRole === 'ADMIN') {
      window.location.href = '/admin'
    } else {
      window.location.href = '/'
    }
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Không thể kết nối đến máy chủ. Vui lòng thử lại sau!'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main 
    class="relative flex min-h-screen items-center justify-center bg-cover bg-center bg-no-repeat px-4 py-8 sm:px-6 lg:px-8"
    style="background-image: url('/bg-login-2.png');"
  >
    <div class="absolute inset-0 bg-slate-900/30 backdrop-blur-[2px]" />
    <div class="relative z-10 grid w-full max-w-5xl overflow-hidden rounded-3xl border border-white/60 bg-cyan-50/85 shadow-2xl shadow-cyan-900/20 backdrop-blur-2xl lg:grid-cols-12">
      
      <!-- LEFT COLUMN -->
      <aside class="relative hidden flex-col justify-between overflow-hidden bg-gradient-to-br from-teal-50/90 via-cyan-50/80 to-white/90 p-10 lg:col-span-5 lg:flex border-r border-cyan-100/50">
        <div class="relative z-10">
          <div class="inline-flex items-center gap-3.5 rounded-2xl border border-teal-100/50 bg-white/60 px-4 py-2.5 backdrop-blur-md shadow-sm">
            <img 
              src="/donga.png" 
              alt="EAUT Official Logo"
              class="size-11 object-contain drop-shadow-sm" 
            />
            <div class="text-left leading-tight">
              <span class="block text-sm font-extrabold uppercase tracking-wider text-teal-700">ClassHub</span>
              <span class="block text-[11px] text-slate-500">Đại Học Công Nghệ Đông Á</span>
            </div>
          </div>

          <h2 class="mt-8 text-3xl font-bold tracking-tight text-slate-800 leading-snug">
            Hệ Thống quản lý <br />
            <span class="bg-gradient-to-r from-teal-600 via-cyan-600 to-blue-600 bg-clip-text text-transparent">Tài sản và Phòng học</span>
          </h2>
          <p class="mt-3 text-sm leading-relaxed text-slate-600">
            Giải pháp tự động hóa trường học
          </p>
        </div>

        <div class="relative z-10 my-8 space-y-3.5">
          <div class="flex items-center gap-3.5 rounded-2xl border border-cyan-100 bg-white/60 p-3.5 backdrop-blur-md shadow-sm">
            <div class="flex size-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-600">
              <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <div>
              <h4 class="text-sm font-bold text-slate-800">Quản lý tài sản thông minh</h4>
              <p class="text-xs text-slate-600">Kiểm soát tự động, tiết kiệm thời gian</p>
            </div>
          </div>

          <div class="flex items-center gap-3.5 rounded-2xl border border-cyan-100 bg-white/60 p-3.5 backdrop-blur-md shadow-sm">
            <div class="flex size-10 shrink-0 items-center justify-center rounded-xl bg-cyan-100 text-cyan-600">
              <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <h4 class="text-sm font-bold text-slate-800">Ủy quyền tiện lợi</h4>
              <p class="text-xs text-slate-600">Mượn/trả tài sản, phòng học dễ dàng</p>
            </div>
          </div>

          <div class="flex items-center gap-3.5 rounded-2xl border border-cyan-100 bg-white/60 p-3.5 backdrop-blur-md shadow-sm">
            <div class="flex size-10 shrink-0 items-center justify-center rounded-xl bg-teal-100 text-teal-600">
              <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h4 class="text-sm font-bold text-slate-800">Giám sát Realtime</h4>
              <p class="text-xs text-slate-600">Cập nhật thời gian thực trạng thái tài sản</p>
            </div>
          </div>
        </div>

        <div class="relative z-10 border-t border-cyan-200/60 pt-4 text-xs text-slate-500">
          © 2026 by Harvey Pham
        </div>
      </aside>

      <!-- RIGHT COLUMN -->
      <section class="flex flex-col justify-center p-8 sm:p-12 lg:col-span-7 bg-white/40">
        <div class="mx-auto w-full max-w-md">
          <div class="mb-8 text-center">
            <img 
              src="/donga.png" 
              alt="EAUT Seal"
              class="mx-auto mb-3 size-16 object-contain drop-shadow-md" 
            />
            <h2 class="text-2xl font-bold text-slate-800 sm:text-3xl">Đăng nhập</h2>
          </div>

          <div 
            v-if="error" 
            class="mb-6 flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-600 animate-shake shadow-sm"
          >
            <svg class="size-5 shrink-0 text-rose-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <span>{{ error }}</span>
          </div>

          <form class="space-y-5" @submit.prevent="login">
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold tracking-wider text-slate-600">
                Mã sinh viên / Email
              </label>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                  <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <input 
                  v-model="msv" 
                  type="text" 
                  required 
                  placeholder="VD: 20231206 hoặc email trường"
                  class="h-12 w-full rounded-2xl border border-cyan-200 bg-white/70 pl-11 pr-4 text-sm text-slate-800 placeholder-slate-400 outline-none transition duration-200 focus:border-teal-500 focus:bg-white focus:ring-4 focus:ring-teal-500/20 shadow-sm"
                />
              </div>
            </div>

            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <label class="block text-xs font-semibold tracking-wider text-slate-600">
                  Mật khẩu
                </label>
                <a href="#" class="text-xs font-medium text-teal-600 hover:text-teal-500 hover:underline">
                  Quên mật khẩu?
                </a>
              </div>
              <div class="relative">
                <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400">
                  <svg class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <input 
                  v-model="mk" 
                  :type="showPassword ? 'text' : 'password'" 
                  required 
                  placeholder="••••••••"
                  class="h-12 w-full rounded-2xl border border-cyan-200 bg-white/70 pl-11 pr-11 text-sm text-slate-800 placeholder-slate-400 outline-none transition duration-200 focus:border-teal-500 focus:bg-white focus:ring-4 focus:ring-teal-500/20 shadow-sm"
                />
                <button 
                  type="button" 
                  @click="showPassword = !showPassword"
                  class="absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400 hover:text-teal-600 transition"
                  tabindex="-1"
                >
                  <svg v-if="!showPassword" class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                  <svg v-else class="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l18 18" />
                  </svg>
                </button>
              </div>
            </div>

            <button 
              type="submit" 
              :disabled="isLoading"
              class="relative mt-2 flex h-12 w-full items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-r from-teal-500 via-cyan-500 to-blue-500 font-bold text-white shadow-lg shadow-cyan-500/30 transition-all duration-300 hover:brightness-110 hover:shadow-cyan-500/40 active:scale-[0.99] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <svg 
                v-if="isLoading" 
                class="size-5 animate-spin mr-2 text-white" 
                fill="none" 
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{{ isLoading ? 'Đang xác thực...' : 'Đăng nhập vào hệ thống' }}</span>
            </button>
          </form>

          <p class="mt-8 text-center text-sm text-slate-500">
            Chưa có tài khoản sinh viên?
            <a href="/register" class="ml-1 font-semibold text-teal-600 transition hover:text-teal-500 hover:underline">
              Đăng ký ngay
            </a>
          </p>
        </div>
      </section>

    </div>
  </main>
</template>

<style scoped>
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-4px); }
  40%, 80% { transform: translateX(4px); }
}
.animate-shake {
  animation: shake 0.4s ease-in-out;
}
</style>
