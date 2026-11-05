<script setup>
import { onMounted, ref } from 'vue'
import { api } from '@/services/apiClient.js'
const props = defineProps({ report: { type: Object, required: true } })
const emit = defineEmits(['saved', 'busy'])
const assignees = ref([]), assignee = ref(props.report.assigneeId || '')
const status = ref(props.report.status || 'PENDING'), blocked = ref(!!props.report.allocationBlocked)
const equipmentId = ref(props.report.equipmentId || ''), sessionId = ref(props.report.sessionId || '')
const note = ref(''), verified = ref(false), busy = ref(false), error = ref('')
onMounted(async () => { try { assignees.value = await api.get('/damage-reports/assignees') } catch (err) { error.value = err.message } })
async function save() {
  if (busy.value) return
  busy.value = true; emit('busy', true); error.value = ''
  try {
    const result = await api.patch(`/damage-reports/${props.report.id}/workflow`, {
      assigneeId: assignee.value || null, unassign: !assignee.value, status: status.value,
      allocationBlocked: blocked.value, verifiedReady: verified.value, note: note.value.trim(),
      equipmentId: equipmentId.value ? Number(equipmentId.value) : null,
      sessionId: sessionId.value ? Number(sessionId.value) : null
    }); emit('saved', result)
  } catch (err) { error.value = err.message }
  finally { busy.value = false; emit('busy', false) }
}
</script>
<template>
  <form class="space-y-3" @submit.prevent="save">
    <p class="text-sm">{{ report.equipmentName }} · {{ report.roomId }}</p>
    <label class="block text-sm">Người phụ trách<select v-model="assignee" :disabled="busy" class="modal-field mt-1 w-full"><option value="">Chưa phân công</option><option v-for="person in assignees" :key="person.id" :value="person.id">{{ person.name }} ({{ person.id }})</option></select></label>
    <label class="block text-sm">Trạng thái<select v-model="status" :disabled="busy" class="modal-field mt-1 w-full"><option value="PENDING">Chờ xử lý</option><option value="IN_PROGRESS">Đang xử lý</option><option value="RESOLVED">Đã xử lý</option></select></label>
    <div class="grid gap-3 sm:grid-cols-2"><label class="text-sm">Mã thiết bị liên quan<input v-model="equipmentId" :disabled="busy" type="number" min="1" class="modal-field mt-1 w-full" /></label><label class="text-sm">Phiếu liên quan<input v-model="sessionId" :disabled="busy" type="number" min="1" class="modal-field mt-1 w-full" /></label></div>
    <label class="flex gap-2 text-sm"><input v-model="blocked" :disabled="busy" type="checkbox" />Chặn cấp phát tại vị trí này</label>
    <p class="text-xs text-slate-500">Đánh dấu đã xử lý không tự gỡ chặn. Phiếu mượn đang có và lịch sử được giữ nguyên.</p>
    <label v-if="report.allocationBlocked && !blocked" class="flex gap-2 text-sm"><input v-model="verified" :disabled="busy" required type="checkbox" />Tôi đã kiểm tra thực tế thiết bị, cửa và điều kiện sẵn sàng cấp phát.</label>
    <label class="block text-sm">Nội dung xử lý<textarea v-model="note" :disabled="busy" required minlength="3" maxlength="1000" rows="3" class="modal-field mt-1 w-full" /></label>
    <p v-if="error" role="alert" class="text-sm text-red-600">{{ error }}</p>
    <button :disabled="busy" class="modal-primary">{{ busy ? 'Đang lưu…' : 'Lưu xử lý sự cố' }}</button>
    <details v-if="report.history?.length" class="text-sm"><summary class="min-h-10 cursor-pointer">Lịch sử xử lý</summary><ol class="space-y-2"><li v-for="(entry, index) in report.history" :key="index" class="rounded-lg bg-slate-50 p-2"><p>{{ entry.actorId || 'Hệ thống' }} · {{ new Date(entry.atUtc).toLocaleString('vi-VN') }}</p><p class="whitespace-pre-wrap break-words">{{ entry.note }}</p></li></ol></details>
  </form>
</template>
