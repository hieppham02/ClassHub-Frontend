<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { api } from '@/services/apiClient.js'
import RfidSummary from './RfidSummary.vue'
const props = defineProps({ sessionId: { type: Number, required: true } })
const rfid = ref(null), error = ref('')
let timer, stopped = false, loading = false
async function refresh() {
  if (loading) return
  loading = true
  try { const result = await api.get(`/operations/sessions/${props.sessionId}/inspection`); if (!stopped) { rfid.value = result.rfid; error.value = '' } }
  catch (err) { if (!stopped) error.value = err.message }
  finally { loading = false }
}
onMounted(() => { refresh(); timer = setInterval(refresh, 3000) })
onUnmounted(() => { stopped = true; clearInterval(timer) })
</script>
<template><div><RfidSummary :value="rfid" /><p v-if="error" role="alert" class="text-sm text-red-600">{{ error }}</p></div></template>
