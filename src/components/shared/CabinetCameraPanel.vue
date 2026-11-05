<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { API_BASE_URL } from '@/config/runtime.js'
import { getToken } from '@/services/authSession.js'
import { CameraFrames } from '@/utils/cameraFrames.js'
const props = defineProps({ cabinetId: { type: Number, required: true } })
defineEmits(['close'])
const canvas = ref(null), state = ref('Đang kết nối camera…'), error = ref(''), frames = ref(0)
let controller, generation = 0
async function start() {
  controller?.abort()
  const current = ++generation
  const request = controller = new AbortController()
  error.value = ''; state.value = 'Đang kết nối camera…'; frames.value = 0
  let reader, timer
  const arm = () => { clearTimeout(timer); timer = setTimeout(() => request.abort('timeout'), 20000) }
  try {
    arm()
    const response = await fetch(API_BASE_URL + '/admin/cabinets/' + props.cabinetId + '/camera/stream', {
      headers: { Authorization: 'Bearer ' + getToken() }, signal: request.signal, cache: 'no-store',
    })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      throw new Error(data?.message || 'Không mở được camera.')
    }
    if (!response.headers.get('content-type')?.includes('application/x-classhub-jpeg-stream'))
      throw new Error('Máy chủ chưa hỗ trợ xem camera.')
    reader = response.body.getReader()
    const decoder = new CameraFrames()
    while (current === generation) {
      arm()
      const chunk = await reader.read()
      if (chunk.done) throw new Error('Camera đã ngắt kết nối.')
      for (const jpeg of decoder.push(chunk.value)) {
        const bitmap = await createImageBitmap(new Blob([jpeg], { type: 'image/jpeg' }))
        try {
          if (current !== generation) return
          const target = canvas.value
          if (!target) return
          target.width = bitmap.width; target.height = bitmap.height
          target.getContext('2d').drawImage(bitmap, 0, 0)
          frames.value++; state.value = bitmap.width + ' × ' + bitmap.height
        } finally { bitmap.close() }
      }
    }
  } catch (e) {
    if (current === generation) {
      error.value = request.signal.reason === 'timeout' ? 'Camera không phản hồi. Hãy thử kết nối lại.' : e.message
      state.value = 'Đã dừng'
    }
  } finally {
    clearTimeout(timer)
    try { await reader?.cancel() } catch {}
    request.abort()
  }
}
function snapshot() {
  canvas.value?.toBlob(blob => {
    if (!blob) return
    const url = URL.createObjectURL(blob), link = document.createElement('a')
    link.href = url; link.download = 'camera-tu-' + props.cabinetId + '-' + Date.now() + '.png'; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }, 'image/png')
}
onMounted(start)
onUnmounted(() => { generation++; controller?.abort() })
</script>
<template>
  <section aria-label="Xem camera" class="mb-5 overflow-hidden rounded-xl border border-slate-200">
    <div class="flex items-center justify-between gap-3 bg-slate-50 px-4 py-3">
      <div><h3 class="font-semibold text-slate-800">Camera trực tiếp</h3><p class="mt-1 text-xs text-slate-500">{{ state }}</p></div>
      <button type="button" class="text-xs font-semibold text-slate-500 hover:text-slate-900" @click="$emit('close')">Đóng camera</button>
    </div>
    <canvas v-show="frames" ref="canvas" width="640" height="480" class="block h-auto w-full bg-slate-950"></canvas>
    <p v-if="error" role="alert" class="px-4 py-5 text-sm text-amber-800">{{ error }}</p>
    <p v-else-if="!frames" class="px-4 py-8 text-center text-sm text-slate-500">Đang chờ hình ảnh từ tủ…</p>
    <div class="flex gap-3 border-t border-slate-100 px-4 py-3">
      <button v-if="error" type="button" class="text-sm font-semibold text-blue-700" @click="start">Kết nối lại</button>
      <button type="button" :disabled="!frames" class="text-sm font-semibold text-blue-700 disabled:opacity-40" @click="snapshot">Chụp và lưu ảnh</button>
    </div>
  </section>
</template>
