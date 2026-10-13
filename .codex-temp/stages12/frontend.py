from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'src/views/client/HomeView.vue';s=p.read_text(encoding='utf-8-sig')
s=s.replace("import BottomNav from '@/components/shared/BottomNav.vue'", "import BottomNav from '@/components/shared/BottomNav.vue'\nimport OperationsPanel from '@/components/shared/OperationsPanel.vue'")
s=s.replace("const danhSachCaHoc = ['Ca 1 (07:00 - 09:30)', 'Ca 2 (09:40 - 12:10)', 'Ca 3 (13:00 - 15:30)', 'Ca 4 (15:40 - 18:10)', 'Ca 5 (18:10 - 20:40)']", "const slots = ref([])\nconst danhSachCaHoc = computed(() => slots.value.map(ca => `${ca.name} (${ca.start} - ${ca.end})`))\nconst selectedSlotId = computed(() => slots.value[danhSachCaHoc.value.indexOf(slot.value)]?.id)\nconst returnCondition = ref('BINH_THUONG')\nconst returnNote = ref('')\nconst returning = ref(false)\nlet sessionTimer\nasync function fetchSlots() {\n  try { slots.value = await api.get('/operations/slots') }\n  catch (err) { triggerError(err.message || 'Không tải được ca học.') }\n}")
start=s.index('        if (!r.equipment) {');end=s.index("        if (!r.floor)",start)
s=s[:start]+"        if (!r.equipment) r.equipment = []\n"+s[end:]
s=s.replace("item.status === 'IN_USE')", "item.status === 'IN_USE' || item.status === 'RETURNING')")
s=s.replace("parseInt(slot.value.match(/\\d+/)[0])", "selectedSlotId.value")
s=s.replace("      caMuon: caSo,\n      vaitro: user.value.role === 'Sinh viên' ? 'SINHVIEN' : 'GIANGVIEN'", "      caMuon: caSo")
s=s.replace('async function returnRoom() {\n  try {', '''async function returnRoom() {
  if (returning.value || !activeBooking.value) return
  if (!['ACTIVE', 'IN_USE', 'RETURNING'].includes(activeBooking.value.status)) return triggerError('Chỉ trả phiên đã nhận thiết bị.')
  returning.value = true
  try {
    if (activeBooking.value.status !== 'RETURNING') {
      await api.put(`/operations/sessions/${activeBooking.value.id}/return-report`, { condition: returnCondition.value, note: returnNote.value })
    }''')
s=s.replace("showSuccessToast('Hoàn tất trả thiết bị thành công!')", "showSuccessToast('Đã yêu cầu khóa tủ. Phiếu chờ quản trị viên kiểm tra trả.')")
s=s.replace("    activeBooking.value = null\n", "")
s=s.replace("async function delegateAccess()", "async function delegateAccess()")
anchor="async function delegateAccess()"
pos=s.index(anchor);before=s[:pos];last=before.rfind("    triggerError(err.message || 'Lỗi kết nối')\n  }\n}")
assert last>=0
before=before[:last]+before[last:].replace("    triggerError(err.message || 'Lỗi kết nối')\n  }\n}","    triggerError(err.message || 'Lỗi kết nối')\n  } finally { returning.value = false }\n}",1);s=before+s[pos:]
s=s.replace('  await fetchRooms()\n', '  await fetchSlots()\n  await fetchRooms()\n',1)
s=s.replace('  // Cập nhật vi phân', '  sessionTimer = setInterval(fetchActiveSession, 30000)\n\n  // Cập nhật vi phân')
s=s.replace('onUnmounted(() => {', 'onUnmounted(() => {\n  clearInterval(sessionTimer)')
s=s.replace('Xác nhận hoàn tất trả thiết bị','Gửi yêu cầu trả thiết bị')
s=s.replace('      <div class="mt-6 flex gap-3">', '''      <select v-model="returnCondition" aria-label="Tình trạng trả" class="mt-4 min-h-11 w-full rounded-xl border border-blue-100 px-3">
        <option value="BINH_THUONG">Bình thường</option><option value="HONG_HOC">Có hỏng hóc</option><option value="MAT_DO">Thiếu thiết bị</option>
      </select>
      <textarea v-model="returnNote" maxlength="2000" placeholder="Mô tả thiết bị hỏng/thiếu" class="mt-3 w-full rounded-xl border border-blue-100 p-3" />
      <div class="mt-6 flex gap-3">''',1)
s=s.replace('<button @click="returnRoom"', '<button :disabled="returning" @click="returnRoom"')
s=s.replace('          <p class="mb-3 text-sm font-bold uppercase tracking-wide text-slate-400">Thiết bị có trong tủ (Bấm để xem ảnh)</p>', '''          <p v-if="activeBooking?.status === 'RETURNING' && activeBooking.room === selectedCabinet.id" class="mb-4 rounded-xl bg-amber-50 p-3 text-sm">Phiếu đang chờ kiểm tra trả. Nếu gửi lệnh khóa thất bại, có thể gửi lại yêu cầu trả.</p>
          <ul v-if="selectedCabinet.equipmentDetails?.length" class="mb-4 space-y-2 text-sm">
            <li v-for="item in selectedCabinet.equipmentDetails" :key="item.id">{{ item.name }} × {{ item.quantity }} · {{ { TOT: 'Tốt', HONG: 'Hỏng', DANG_BAO_TRI: 'Đang bảo trì' }[item.condition] || item.condition }}<p v-if="item.note" class="text-xs text-slate-500">{{ item.note }}</p></li>
          </ul>
          <p class="mb-3 text-sm font-bold uppercase tracking-wide text-slate-400">Danh mục thiết bị của phòng</p>''')
s=s.replace('    <BottomNav :currentPath=', '    <div class="mx-auto max-w-7xl px-4"><OperationsPanel /></div>\n    <BottomNav :currentPath=')
p.write_text(s,encoding='utf-8')
p=root/'src/views/admin/DashboardView.vue';s=p.read_text(encoding='utf-8-sig');s=s.replace("import AdminLayout from '@/components/admin/layout/AdminLayout.vue'", "import AdminLayout from '@/components/admin/layout/AdminLayout.vue'\nimport OperationsPanel from '@/components/shared/OperationsPanel.vue'");s=s.replace('        <!-- Filter thời gian -->','        <OperationsPanel admin />\n\n        <!-- Filter thời gian -->');p.write_text(s,encoding='utf-8')
print('Updated home and admin dashboard.')
