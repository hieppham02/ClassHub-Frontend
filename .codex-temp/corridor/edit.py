from pathlib import Path

root = Path('.codex-temp/corridor/backend')
def edit(path, old, new):
    p = Path(path)
    s = p.read_text(encoding='utf-8-sig')
    assert old in s, (path, old[:60])
    p.write_text(s.replace(old, new, 1), encoding='utf-8')

edit(root/'Models/PhongHoc.cs', '        [Column("building_id")]', '        [Column("location_type"), MaxLength(20)]\n        public string LocationType { get; set; } = "ROOM";\n\n        [Column("building_id")]')
edit(root/'Controllers/RoomsController.cs', '                    name = room.ten_phong,', '                    name = room.ten_phong,\n                    locationType = room.LocationType,')
edit(root/'Controllers/AssetsController.cs', 'name=r.ten_phong, buildingId=r.ma_toa_nha,', 'name=r.ten_phong, locationType=r.LocationType, buildingId=r.ma_toa_nha,')
edit(root/'Controllers/AdminBuildingsController.cs', 'rooms = building.PhongHocs.Count,', 'rooms = building.PhongHocs.Count(r => r.LocationType == "ROOM"),')
edit(root/'Controllers/AdminBuildingsController.cs', 'var rooms = await _context.phong_hoc\n                .AsNoTracking()', 'var rooms = await _context.phong_hoc\n                .Where(room => room.LocationType == "ROOM")\n                .AsNoTracking()')

edit('src/views/client/HomeView.vue', "const selectedCabinet = ref(null)", """const selectedCabinet = ref(null)
const damageLocation = ref(null)
const damageEquipment = ref('')
const damageDescription = ref('')
const sendingDamage = ref(false)
function openDamageReport(location) {
  damageLocation.value = location
  damageEquipment.value = ''; damageDescription.value = ''
}
async function sendDamageReport() {
  if (sendingDamage.value) return
  sendingDamage.value = true
  try {
    await api.post('/damage-reports', { roomId: damageLocation.value.id, equipmentName: damageEquipment.value.trim(), description: damageDescription.value.trim() })
    damageLocation.value = null
    showSuccessToast('Đã gửi báo cáo hỏng hóc cho quản trị viên.')
  } catch (err) { triggerError(err.message || 'Không gửi được báo cáo.') }
  finally { sendingDamage.value = false }
}
""")
edit('src/views/client/HomeView.vue', "showSuccessToast('Đăng ký phòng thành công!')", "showSuccessToast(room.locationType === 'CORRIDOR' ? 'Đăng ký mượn tủ hành lang thành công!' : 'Đăng ký phòng thành công!')")
edit('src/views/client/HomeView.vue', "'bg-red-400 border-red-600 opacity-80': getCabinetStatus(cab) === 'MAINTENANCE'", "'bg-red-400 border-red-600 opacity-80': getCabinetStatus(cab) === 'MAINTENANCE',\n                    'corridor-cabinet': cab.locationType === 'CORRIDOR'")
edit('src/views/client/HomeView.vue', '<div class="flex flex-col gap-1 w-full px-2 sm:px-3 opacity-30">', '''<span v-if="cab.locationType === 'CORRIDOR'" class="text-[10px] font-bold text-slate-800">Hành lang · Đồ dùng chung</span>
                  <div v-if="cab.locationType === 'CORRIDOR'" class="corridor-doors" aria-hidden="true"><span></span><span></span></div>
                  <div v-else class="flex flex-col gap-1 w-full px-2 sm:px-3 opacity-30">''')
edit('src/views/client/HomeView.vue', ":title=\"'Tủ thiết bị ' + selectedCabinet.name\"", ":title=\"selectedCabinet.locationType === 'CORRIDOR' ? selectedCabinet.name : 'Tủ thiết bị ' + selectedCabinet.name\"")
edit('src/views/client/HomeView.vue', 'Danh mục thiết bị của phòng</p>', "{{ selectedCabinet.locationType === 'CORRIDOR' ? 'Đồ dùng chung · Hành lang' : 'Danh mục thiết bị của phòng' }}</p>\n          <p v-if=\"selectedCabinet.locationType === 'CORRIDOR'\" class=\"mb-4 text-sm text-slate-500\">Ổ điện, cáp mạng LAN, phấn viết bảng. Quy trình mượn và trả giống tủ phòng học.</p>")
edit('src/views/client/HomeView.vue', '<template #footer><button type="button" @click="selectedCabinet = null;', '<template #footer><button type="button" class="modal-cancel text-red-600" @click="openDamageReport(selectedCabinet)">Báo hỏng hóc</button><button type="button" @click="selectedCabinet = null;')
edit('src/views/client/HomeView.vue', '    <AppModal v-if="selectedCabinet"', '''    <AppModal v-if="damageLocation" title="Báo cáo hỏng hóc" layer="confirm" @close="!sendingDamage && (damageLocation = null)">
      <form id="damage-report-form" @submit.prevent="sendDamageReport" class="space-y-4">
        <p class="text-sm text-slate-500">{{ damageLocation.name }} · {{ damageLocation.floor }} · {{ damageLocation.building }}</p>
        <label class="block text-sm font-semibold">Thiết bị hỏng<input v-model="damageEquipment" required maxlength="100" class="modal-field mt-2 w-full" placeholder="Ví dụ: ổ điện, máy chiếu..." /></label>
        <label class="block text-sm font-semibold">Mô tả hỏng hóc<textarea v-model="damageDescription" required minlength="10" maxlength="2000" rows="5" class="modal-field mt-2 w-full" placeholder="Mô tả hiện tượng và vị trí thiết bị..." /></label>
        <p class="text-xs text-slate-500">Báo cáo sẽ được gửi cho quản trị viên để kiểm tra và xử lý.</p>
      </form>
      <template #footer><button class="modal-cancel" :disabled="sendingDamage" @click="damageLocation = null">Hủy</button><button form="damage-report-form" type="submit" class="modal-primary" :disabled="sendingDamage">{{ sendingDamage ? 'Đang gửi...' : 'Gửi báo cáo' }}</button></template>
    </AppModal>
    <AppModal v-if="selectedCabinet"''')
with Path('src/views/client/HomeView.vue').open('a', encoding='utf-8') as f:
    f.write('''\n<style scoped>
.corridor-cabinet { grid-column: span 2; height: 180px; }
.corridor-doors { display: flex; gap: 8px; width: 88%; height: 95px; }
.corridor-doors span { flex: 1; border: 2px solid #ffffff90; border-radius: 6px; position: relative; }
.corridor-doors span::after { content: ''; position: absolute; right: 8px; top: 40%; height: 25px; width: 4px; background: white; border-radius: 4px; }
</style>\n''')

edit('src/views/admin/AssetsView.vue', 'const rooms = ref([])', '''const rooms = ref([])
const damageReports = ref([])
const reportFilter = ref('')
const resolvingReport = ref(null)
const resolutionNote = ref('')
const scopedReports = computed(() => {
  const ids = new Set(rooms.value.filter(r => (!building.value || r.buildingId === building.value) && (!floor.value || String(r.floor) === floor.value)).map(r => r.id))
  return damageReports.value.filter(r => ids.has(r.roomId))
})
const reportCards = computed(() => [
  { label: 'Toàn bộ cảnh báo', key: '', count: scopedReports.value.length },
  { label: 'Đã xử lý', key: 'RESOLVED', count: scopedReports.value.filter(r => r.status === 'RESOLVED').length },
  { label: 'Chưa xử lý', key: 'PENDING', count: scopedReports.value.filter(r => r.status === 'PENDING').length }
])
const roomReports = computed(() => damageReports.value.filter(r => r.roomId === roomId.value && (!reportFilter.value || r.status === reportFilter.value)))
const { page: reportPage, pageItems: reportPageItems, totalItems: reportTotal } = usePagination(roomReports, [roomId, reportFilter])
async function resolveDamageReport() {
  if (busy.value) return
  busy.value = true; error.value = ''
  try {
    await api.patch(`/damage-reports/${resolvingReport.value.id}/resolve`, { note: resolutionNote.value.trim() })
    resolvingReport.value = null
    await refresh(true)
    success.value = 'Đã cập nhật kết quả xử lý.'
  } catch (err) { error.value = err.message }
  finally { busy.value = false }
}
const assetPieColors = ['#059669', '#dc2626', '#d97706', '#64748b']
const assetPieStyle = computed(() => {
  const total = assetOverview.value[0].value
  let angle = 0
  const stops = assetOverview.value.slice(1).map((item, i) => {
    const start = angle; angle += total ? item.value / total * 360 : 0
    return `${assetPieColors[i]} ${start}deg ${angle}deg`
  })
  return { background: total ? `conic-gradient(${stops.join(',')})` : '#e2e8f0' }
})''')
edit('src/views/admin/AssetsView.vue', "const data = await api.get('/admin/assets')", "const [data, reports] = await Promise.all([api.get('/admin/assets'), api.get('/damage-reports')])")
edit('src/views/admin/AssetsView.vue', 'rooms.value = data.rooms; equipment.value', 'damageReports.value = reports\n    rooms.value = data.rooms; equipment.value')
old='''          <div class="asset-summary-grid">
            <div v-for="item in assetOverview" :key="item.label" class="iot-status-tile">
              <p class="iot-status-label"><span :class="item.color" aria-hidden="true">●</span>{{ item.label }}</p>
              <div class="flex items-baseline gap-2">
                <strong :class="item.color">{{ item.value }}</strong>
                <span class="text-xs text-slate-500">thiết bị</span>
              </div>
            </div>
          </div>'''
new='''          <div class="asset-overview-layout">
            <div class="asset-pie-panel">
              <div class="asset-pie" :style="assetPieStyle" role="img" :aria-label="assetOverview.map(item => `${item.label}: ${item.value}`).join(', ')"><div><strong>{{ assetOverview[0].value }}</strong><span>tài sản</span></div></div>
              <div class="space-y-3"><div v-for="(item, i) in assetOverview.slice(1)" :key="item.label" class="flex items-center gap-2 text-sm"><span class="size-2.5 rounded-full" :style="{ background: assetPieColors[i] }"></span><span class="text-slate-500">{{ item.label }}</span><strong class="ml-auto pl-4">{{ item.value }}</strong></div></div>
            </div>
            <div class="damage-summary-grid"><button v-for="card in reportCards" :key="card.label" @click="reportFilter = card.key" :aria-pressed="reportFilter === card.key" class="iot-status-tile text-left" :class="{ 'ring-2 ring-brand': reportFilter === card.key }"><p class="iot-status-label">{{ card.label }}</p><strong :class="card.key === 'PENDING' ? 'text-red-600' : card.key === 'RESOLVED' ? 'text-emerald-600' : 'text-ink'">{{ card.count }}</strong><p class="mt-2 text-xs text-slate-500">Báo cáo hỏng hóc</p></button></div>
          </div>'''
edit('src/views/admin/AssetsView.vue', old, new)
edit('src/views/admin/AssetsView.vue', '<template v-else-if="tab === \'assets\'">', '''<template v-else-if="tab === 'assets'">
              <section class="asset-table-card mb-5 p-5">
                <h3 class="mb-2 text-sm font-semibold text-ink">Báo cáo hỏng hóc · {{ selectedRoom?.name || 'Chưa chọn vị trí' }}</h3>
                <p class="mb-4 text-xs text-slate-500">{{ reportCards.find(c => c.key === reportFilter)?.label }} · {{ roomReports.length }} báo cáo tại vị trí này</p>
                <article v-for="report in reportPageItems" :key="report.id" class="border-t border-slate-100 py-4">
                  <div class="flex flex-wrap items-center justify-between gap-2"><strong class="text-sm">{{ report.equipmentName }}</strong><span class="rounded-full px-2 py-1 text-xs" :class="report.status === 'RESOLVED' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'">{{ report.status === 'RESOLVED' ? 'Đã xử lý' : 'Chưa xử lý' }}</span></div>
                  <p class="mt-2 whitespace-pre-wrap break-words text-sm text-slate-600">{{ report.description }}</p>
                  <p class="mt-2 text-xs text-slate-400">{{ report.reporterId }} · {{ dateTime(report.createdAt) }}</p>
                  <p v-if="report.status === 'RESOLVED'" class="mt-2 whitespace-pre-wrap text-sm text-emerald-700">Kết quả: {{ report.resolutionNote }} · {{ dateTime(report.resolvedAt) }}</p>
                  <button v-else class="mt-3 text-sm font-semibold text-brand" :disabled="busy" @click="resolvingReport = report; resolutionNote = ''">Đánh dấu đã xử lý</button>
                </article>
                <p v-if="!roomReports.length" class="py-4 text-sm text-slate-400">Không có báo cáo phù hợp tại vị trí này.</p>
                <TablePagination v-model:page="reportPage" :total-items="reportTotal" />
              </section>''')
edit('src/views/admin/AssetsView.vue', '<span class="text-sm font-semibold">{{ r.name }}</span>', '<span class="text-sm font-semibold">{{ r.name }}<span v-if="tab === \'assets\' && damageReports.some(report => report.roomId === r.id && report.status === \'PENDING\')" class="ml-2 text-xs text-red-600">● Báo hỏng</span></span>')
edit('src/views/admin/AssetsView.vue', 'Chọn phòng học</h2>', 'Chọn phòng / tủ hành lang</h2>')
edit('src/views/admin/AssetsView.vue', '    <div class="w-full iot-workspace"', '''    <AppModal v-if="resolvingReport" title="Xử lý báo cáo hỏng hóc" @close="!busy && (resolvingReport = null)">
      <form id="resolve-report-form" @submit.prevent="resolveDamageReport"><p class="mb-3 text-sm">{{ resolvingReport.equipmentName }} · {{ roomName(resolvingReport.roomId) }}</p><label class="block text-sm font-semibold">Kết quả xử lý<textarea v-model="resolutionNote" required minlength="3" maxlength="1000" rows="4" class="modal-field mt-2 w-full" /></label><p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p></form>
      <template #footer><button class="modal-cancel" :disabled="busy" @click="resolvingReport = null">Hủy</button><button form="resolve-report-form" type="submit" class="modal-primary" :disabled="busy">{{ busy ? 'Đang lưu...' : 'Xác nhận đã xử lý' }}</button></template>
    </AppModal>
    <div class="w-full iot-workspace"''')
with Path('src/views/admin/AssetsView.vue').open('a', encoding='utf-8') as f:
    f.write('''\n<style scoped>
.asset-overview-layout { display: grid; grid-template-columns: minmax(320px, 1fr) minmax(0, 1.2fr); gap: 24px; align-items: center; }
.asset-pie-panel { display: flex; align-items: center; gap: 24px; }
.asset-pie { width: 160px; height: 160px; border-radius: 50%; display: grid; place-items: center; flex-shrink: 0; }
.asset-pie > div { width: 112px; height: 112px; background: white; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.asset-pie strong { font-size: 28px; } .asset-pie span { color: #64748b; font-size: 12px; }
.damage-summary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
@media (max-width: 1100px) { .asset-overview-layout { grid-template-columns: 1fr; } }
@media (max-width: 480px) { .asset-pie-panel { gap: 12px; } .asset-pie { width: 125px; height: 125px; } .asset-pie > div { width: 88px; height: 88px; } .damage-summary-grid { grid-template-columns: 1fr; } }
</style>\n''')
