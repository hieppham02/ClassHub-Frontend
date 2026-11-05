<script setup>
import { onMounted, ref } from 'vue'
import { api } from '@/services/apiClient.js'
const props = defineProps({ equipment: { type: Object, required: true } })
const tags = ref([]), uid = ref(''), error = ref(''), busy = ref(false)
async function refresh() {
  try { tags.value = await api.get(`/operations/equipment/${props.equipment.id}/rfid`); error.value = '' }
  catch (err) { error.value = err.message }
}
async function add() {
  busy.value = true; error.value = ''
  try { await api.post(`/operations/equipment/${props.equipment.id}/rfid`, { uid: uid.value.trim().toUpperCase() }); uid.value = ''; await refresh() }
  catch (err) { error.value = err.message }
  finally { busy.value = false }
}
async function remove(tag) {
  busy.value = true; error.value = ''
  try { await api.delete(`/operations/equipment/${props.equipment.id}/rfid/${encodeURIComponent(tag.uid)}`); await refresh() }
  catch (err) { error.value = err.message }
  finally { busy.value = false }
}
onMounted(refresh)
</script>
<template>
  <section class="space-y-2 rounded-lg bg-slate-50 p-3 text-sm sm:col-span-2">
    <p class="font-medium">Thẻ RFID: {{ tags.length }} / {{ equipment.quantity }}</p>
    <p class="text-xs text-slate-500">Quét từng thẻ trên trang thiết bị tủ rồi nhập UID. Một UID gắn với một món.</p>
    <p v-if="error" role="alert" class="text-red-600">{{ error }}</p>
    <div v-for="tag in tags" :key="tag.uid" class="flex items-center justify-between gap-2"><code>{{ tag.uid }}</code><button :disabled="busy" @click="remove(tag)" class="min-h-11 px-3 text-red-700">Gỡ thẻ</button></div>
    <form class="flex flex-wrap gap-2" @submit.prevent="add">
      <input v-model="uid" maxlength="20" pattern="[0-9A-Fa-f]{8}|[0-9A-Fa-f]{14}|[0-9A-Fa-f]{20}" required placeholder="UID: 8, 14 hoặc 20 ký tự hex" aria-label="UID thẻ RFID" class="min-h-11 min-w-48 flex-1 rounded-lg border border-slate-200 px-3 uppercase" />
      <button :disabled="busy || tags.length >= equipment.quantity" class="min-h-11 rounded-xl border border-blue-200 px-3 disabled:opacity-50">Gắn thẻ</button>
    </form>
  </section>
</template>
