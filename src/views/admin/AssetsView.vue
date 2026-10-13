<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AdminLayout from '@/components/admin/layout/AdminLayout.vue'
import AdminPageTitle from '@/components/admin/layout/AdminPageTitle.vue'
import AppModal from '@/components/shared/AppModal.vue'
import TablePagination from '@/components/shared/TablePagination.vue'
import { usePagination } from '@/composables/usePagination.js'
import { api } from '@/services/apiClient.js'
import { createDemoStatuses } from '@/utils/iotDemoStatus.js'

const uiText = {
  noTelemetry: 'Chưa có mẫu cảm biến trong khoảng xem.',
  bulkTracking: 'Theo số lượng',
  quantity: 'Số lượng',
  confirm: 'Xác nhận'
}

function borrowingLabel(node) {
  const active = powerStates.value[node.id]?.roomHasActiveBorrowing
  if (active === true) return 'Có lượt mượn đang diễn ra'
  if (active === false) return 'Không có lượt mượn đang diễn ra'
  return 'Chưa xác định lượt mượn'
}

const route = useRoute()
const router = useRouter()
const tabs = [{ id: 'iot', name: 'Giám sát IoT' }, { id: 'assets', name: 'Tài sản' }, { id: 'warehouse', name: 'Kho thiết bị' }]
const tab = ref(route.query.tab === 'allocation' ? 'warehouse' : tabs.some(t => t.id === route.query.tab) ? route.query.tab : 'iot')
const roomId = ref(String(route.query.room || ''))
const search = ref('')
const building = ref('')
const floor = ref('')
const roomSearch = ref('')
const conditionFilter = ref('')
const catalogs = ref([])
const catalogFilter = ref('')
const receiptSearch = ref('')
const receiptCatalogs = computed(() => {
  const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLowerCase().trim()
  const query = normalize(receiptSearch.value)
  return catalogs.value.filter(c => c.enabled && (String(c.id) === String(form.catalogId) || normalize(`${c.name} ${c.category}`).includes(query)))
})
const catalogEnabledFilter = ref('')
const stockCatalogId = ref(null)
const stockConditionFilter = ref('')
function showWarehouseDetails(id) { stockCatalogId.value = id; stockConditionFilter.value = '' }
const rooms = ref([])
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
})
const equipment = ref([])
const nodes = ref([])
const nodeFilter = ref('')
function matchesNodeFilter(node) { return !nodeFilter.value || (nodeFilter.value === 'ACTIVE' ? node.status !== 'DISABLED' : node.status === nodeFilter.value) }
const powerStates = ref({})
const statisticsNodes = computed(() => {
  const roomIds = new Set(rooms.value.filter(r => (!building.value || r.buildingId === building.value) && (!floor.value || String(r.floor) === floor.value)).map(r => r.id))
  return nodes.value.filter(n => roomIds.has(n.roomId))
})
const nodeStatisticsScope = computed(() => building.value || floor.value ? 'Lọc theo tòa nhà / tầng' : 'Tất cả phòng')
const nodeTotals = computed(() => ({ active: statisticsNodes.value.filter(n => n.status !== 'DISABLED').length, online: statisticsNodes.value.filter(n => n.status === 'ONLINE').length, offline: statisticsNodes.value.filter(n => n.status === 'OFFLINE').length, maintenance: statisticsNodes.value.filter(n => n.status === 'DISABLED').length }))
const nodeSegments = computed(() => [
  { key: '', label: 'Tất cả phòng', count: rooms.value.filter(r => r.locationType !== 'CORRIDOR' && (!building.value || r.buildingId === building.value) && (!floor.value || String(r.floor) === floor.value)).length, unit: 'phòng', color: '#0969c7' },
  { key: 'ONLINE', label: 'Trực tuyến', count: nodeTotals.value.online, unit: 'node', color: '#059669' },
  { key: 'OFFLINE', label: 'Ngoại tuyến', count: nodeTotals.value.offline, unit: 'node', color: '#64748b' },
  { key: 'DISABLED', label: 'Bảo trì', count: nodeTotals.value.maintenance, unit: 'node', color: '#d97706' }
])
const roomConnections = computed(() => Object.fromEntries(rooms.value.map(room => {
  const items = nodes.value.filter(node => node.roomId === room.id)
  return [room.id, { total: items.length, online: items.filter(node => node.status === 'ONLINE').length }]
})))
const metricIcons = {
  current: 'M13 2 4 14h7l-1 8 10-12h-7l1-8Z',
  temperature: 'M9 14.5V5a3 3 0 0 1 6 0v9.5a5 5 0 1 1-6 0ZM12 8v9',
  humidity: 'M12 3s-7 8-7 12a7 7 0 0 0 14 0c0-4-7-12-7-12ZM8 15a4 4 0 0 0 4 4',
  airquality: 'M3 8h12a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h5a3 3 0 1 1-3 3'
}
async function saveNode(node, event) {
  const previous = node.status === 'DISABLED' ? 'DISABLED' : 'ACTIVE'
  const status = event.target.value
  if (busy.value || status === previous) return
  busy.value = true; error.value = ''
  try {
    await api.patch(`/admin/assets/nodes/${node.id}/status`, { status })
    await refresh(true)
  } catch (err) { event.target.value = previous; error.value = err.message }
  finally { busy.value = false }
}

let powerRequestId = 0
const powerLabels = {
  UNKNOWN: 'Đang tải số đo',
  NO_DATA: 'Chưa nhận được số đo dòng điện',
  LOW: 'Tiêu thụ thấp (dưới 1A)',
  IN_USE: 'Có sử dụng điện trong thời gian mượn',
  OBSERVING: 'Có sử dụng điện ngoài lịch — đang theo dõi',
  OUT_OF_SCHEDULE: 'Điện ngoài lịch kéo dài — kiểm tra thiết bị chưa tắt'
}
async function loadPower() {
  const sequence = ++powerRequestId
  const results = await Promise.all(selectedNodes.value.map(async node => {
    try { return [node.id, await api.get(`/admin/assets/nodes/${node.id}/power`)] }
    catch { return [node.id, { state: 'UNKNOWN', roomHasActiveBorrowing: null }] }
  }))
  if (sequence === powerRequestId) powerStates.value = Object.fromEntries(results)
}
const loading = ref(false)
const error = ref('')
const success = ref('')
const busy = ref(false)
const modal = ref(null)
const selectedAsset = ref(null)
const form = reactive({ name: '', category: 'Khác', quantity: 1, trackingMode: 'BULK', assetCode: '', condition: 'HONG', note: '', targetRoomId: '', actualCount: 0, catalogId: '', stockId: '', enabled: true })
const conditions = { TOT: 'Sử dụng tốt', HONG: 'Hỏng', DANG_BAO_TRI: 'Đang bảo trì', NGUNG_SU_DUNG: 'Ngừng sử dụng' }
const assetConditionClasses = {
  TOT: 'bg-emerald-50 text-emerald-700',
  HONG: 'bg-red-50 text-red-700',
  DANG_BAO_TRI: 'bg-amber-50 text-amber-700',
  NGUNG_SU_DUNG: 'bg-slate-100 text-slate-600'
}
const actions = { CATALOG_CREATE: 'Thêm danh mục thiết bị', CATALOG_EDIT: 'Sửa danh mục thiết bị', CATALOG_DELETE: 'Xóa danh mục thiết bị', ADD_ROOM: 'Thêm thiết bị vào phòng', ROOM_QUANTITY: 'Thay đổi số lượng tại phòng', RECEIPT: 'Nhập kho', ALLOCATE: 'Phân bổ vào phòng', RETURN: 'Thu hồi về kho', TRANSFER: 'Điều chuyển phòng', CONDITION: 'Báo / đổi tình trạng', COUNT: 'Kiểm kê' }
const metrics = [{ key: 'current', name: 'Dòng điện tổng phòng', unit: 'A' }, { key: 'temperature', name: 'Nhiệt độ', unit: '°C' }, { key: 'humidity', name: 'Độ ẩm', unit: '%' }, { key: 'airquality', name: 'Chất lượng không khí', unit: 'index' }]
let refreshTimer
let requestId = 0
const selectedRoom = computed(() => rooms.value.find(r => r.id === roomId.value))
const selectedNodes = computed(() => nodes.value.filter(n => n.roomId === roomId.value))
const roomLastSeenAt = computed(() => selectedNodes.value.reduce((latest, node) => {
  const timestamp = node.lastSeenAt ? Date.parse(node.lastSeenAt) : NaN
  return Number.isFinite(timestamp) && (!latest || timestamp > Date.parse(latest)) ? node.lastSeenAt : latest
}, null))
const visibleNodes = computed(() => selectedNodes.value.filter(matchesNodeFilter))
const assetOverview = computed(() => {
  const roomIds = new Set(rooms.value.filter(r => (!building.value || r.buildingId === building.value) && (!floor.value || String(r.floor) === floor.value)).map(r => r.id))
  const items = equipment.value.filter(e => roomIds.has(e.roomId))
  const sum = condition => items.filter(e => !condition || e.condition === condition).reduce((total, e) => total + e.quantity, 0)
  return [{ label: 'Tài sản tại phòng', value: sum(), color: 'text-ink' }, { label: 'Sử dụng tốt', value: sum('TOT'), color: 'text-emerald-600' }, { label: 'Hỏng', value: sum('HONG'), color: 'text-red-600' }, { label: 'Đang bảo trì', value: sum('DANG_BAO_TRI'), color: 'text-amber-600' }, { label: 'Ngừng sử dụng', value: sum('NGUNG_SU_DUNG'), color: 'text-slate-600' }]
})
const demoStatuses = computed(() => createDemoStatuses(nodes.value, rooms.value, metrics))
const metricStates = {
  stable: { label: 'Ổn định', classes: 'border-emerald-200 bg-emerald-50 text-emerald-700' },
  warning: { label: 'Cảnh báo', classes: 'border-amber-200 bg-amber-50 text-amber-700' },
  critical: { label: 'Cần xử lý ngay', classes: 'border-red-200 bg-red-50 text-red-700' },
  unknown: { label: 'Chưa đánh giá', classes: 'border-slate-200 bg-slate-50 text-slate-500' }
}
function metricState(node, key) {
  if (key === 'current') {
    const state = powerStates.value[node.id]?.state
    if (state === 'LOW' || state === 'IN_USE') return metricStates.stable
    if (state === 'OUT_OF_SCHEDULE') return metricStates.warning
    return { label: state === 'NO_DATA' ? 'Chưa có số đo' : 'Theo dõi tiêu thụ', classes: 'border-emerald-200 bg-emerald-50 text-emerald-700' }
  }
  return metricStates[demoStatuses.value.get(`${node.id}:${key}`) || 'unknown']
}
function nodeDisplayName(node) {
  return node.dataSource === 'MOCK' ? ` ${rooms.value.find(r => r.id === node.roomId)?.name || node.roomId}` : node.name
}
function nodeDisplayCode(node) {
  return node.nodeCode.replace(/-MOCK(?=-|$)/gi, '')
}
const buildings = computed(() => [...new Map(rooms.value.map(r => [r.buildingId, r.building])).entries()])
const floors = computed(() => [...new Set(rooms.value.filter(r => !building.value || r.buildingId === building.value).map(r => r.floor))].sort((a, b) => a - b))
const filteredRooms = computed(() => rooms.value.filter(r => (tab.value !== 'iot' || r.locationType !== 'CORRIDOR') && (!building.value || r.buildingId === building.value) && (!floor.value || String(r.floor) === floor.value) && (!roomSearch.value || `${r.name} ${r.id}`.toLowerCase().includes(roomSearch.value.toLowerCase())) && (tab.value !== 'iot' || !nodeFilter.value || nodes.value.some(n => n.roomId === r.id && matchesNodeFilter(n)))))
watch(filteredRooms, list => { if (tab.value === 'iot' && nodeFilter.value && !list.some(r => r.id === roomId.value)) roomId.value = list[0]?.id || '' })
const roomInventory = computed(() => equipment.value.filter(e => e.roomId === roomId.value))
const needsAttention = computed(() => roomInventory.value.filter(e => e.condition !== 'TOT').reduce((total, e) => total + e.quantity, 0))
const warehouseCount = computed(() => equipment.value.filter(e => !e.roomId && e.usageScope === 'ROOM' && e.condition === 'TOT').reduce((total, e) => total + e.quantity, 0))
const filteredAssets = computed(() => roomInventory.value.filter(e => (!conditionFilter.value || e.condition === conditionFilter.value) && (!search.value || `${e.name} ${e.assetCode || ''} ${e.category}`.toLowerCase().includes(search.value.toLowerCase()))))
const { page, pageItems, totalItems } = usePagination(filteredAssets, [tab, roomId, search, conditionFilter])
const catalogRows = computed(() => catalogs.value.map(c => {
  const items = equipment.value.filter(e => e.catalogId === c.id)
  const total = items.reduce((sum, e) => sum + e.quantity, 0)
  const allocated = items.filter(e => e.roomId).reduce((sum, e) => sum + e.quantity, 0)
  return { ...c, total, allocated, inStock: total - allocated, available: items.filter(e => !e.roomId && e.condition === 'TOT').reduce((sum, e) => sum + e.quantity, 0) }
}).filter(c => (!catalogFilter.value || c.category === catalogFilter.value) && (!catalogEnabledFilter.value || String(c.enabled) === catalogEnabledFilter.value) && (!search.value || `${c.name} ${c.category}`.toLowerCase().includes(search.value.toLowerCase()))))
const { page: catalogPage, pageItems: catalogPageItems, totalItems: catalogTotal } = usePagination(catalogRows, [search, catalogFilter, catalogEnabledFilter])
const warehouseStock = computed(() => equipment.value.filter(e => !e.roomId && (!stockCatalogId.value || e.catalogId === stockCatalogId.value) && (!stockConditionFilter.value || e.condition === stockConditionFilter.value)))
const { page: stockPage, pageItems: stockPageItems, totalItems: stockTotal } = usePagination(warehouseStock, [stockCatalogId, stockConditionFilter])
const selectedStock = computed(() => equipment.value.find(e => String(e.id) === String(form.stockId)))
const availableStock = computed(() => equipment.value.filter(e => !e.roomId && e.condition === 'TOT' && catalogs.value.some(c => c.id === e.catalogId && c.enabled)))
const selectedReceiptCatalog = computed(() => catalogs.value.find(c => String(c.id) === String(form.catalogId)))
const warehouseSummary = computed(() => [
  { label: 'Danh mục thiết bị', value: catalogs.value.length, color: 'text-ink' },
  { label: 'Tổng số lượng', value: equipment.value.reduce((sum, e) => sum + e.quantity, 0), color: 'text-brand' },
  { label: 'Đã cấp cho phòng', value: equipment.value.filter(e => e.roomId).reduce((sum, e) => sum + e.quantity, 0), color: 'text-emerald-600' },
  { label: 'Còn trong kho', value: equipment.value.filter(e => !e.roomId).reduce((sum, e) => sum + e.quantity, 0), color: 'text-slate-600' },
  { label: 'Kho cần xử lý', value: equipment.value.filter(e => !e.roomId && e.condition !== 'TOT').reduce((sum, e) => sum + e.quantity, 0), color: 'text-amber-600' }
])
const { page: roomPage, pageItems: roomPageItems, totalItems: roomTotal } = usePagination(filteredRooms, [building, floor, roomSearch, nodeFilter, tab])
const logs = ref([])
const logPage = ref(1)
const logTotal = ref(0)
let logRequestId = 0

function roomName(id) { return id ? (rooms.value.find(r => r.id === id)?.name || id) : 'Kho' }
function dateTime(value) { return value ? new Date(value).toLocaleString('vi-VN') : 'Chưa nhận dữ liệu' }
function countInRoom(id) { return equipment.value.filter(e => e.roomId === id).reduce((sum, e) => sum + e.quantity, 0) }
async function refresh(silent = false) {
  const sequence = ++requestId
  if (!silent) { loading.value = true; error.value = '' }
  try {
    const [data, reports] = await Promise.all([api.get('/admin/assets'), api.get('/damage-reports')])
    if (sequence !== requestId) return
    damageReports.value = reports
    rooms.value = data.rooms; equipment.value = data.equipment; nodes.value = data.nodes; catalogs.value = data.catalogs || []
    if (!rooms.value.some(r => r.id === roomId.value && (tab.value !== 'iot' || r.locationType !== 'CORRIDOR'))) roomId.value = rooms.value.find(r => tab.value !== 'iot' || r.locationType !== 'CORRIDOR')?.id || ''
    await loadPower()
  } catch (err) { if (sequence === requestId) error.value = err.message || 'Không tải được tài sản.' }
  finally { if (sequence === requestId) loading.value = false }
}
async function loadHistory() {
  const sequence = ++logRequestId
  try {
    const params = new URLSearchParams({ page: String(logPage.value) })
    if (roomId.value && tab.value !== 'warehouse') params.set('roomId', roomId.value)
    const data = await api.get(`/admin/assets/history?${params}`)
    if (sequence !== logRequestId) return
    logs.value = data.items.map(log => {
      let detail = {}; try { detail = JSON.parse(log.details || '{}') } catch { /* Older logs may be plain text. */ }
      return { ...log, detail }
    })
    logTotal.value = data.totalItems
  } catch (err) { if (sequence === logRequestId) error.value = err.message }
}
watch([tab, roomId], () => {
  router.replace({ query: { ...route.query, room: roomId.value || undefined, tab: tab.value } })
})
watch(roomId, () => { logPage.value = 1; loadHistory(); samples.value = []; chartNodeId.value = '' })
watch(logPage, loadHistory)
watch(tab, () => { if (tab.value === 'iot' && selectedRoom.value?.locationType === 'CORRIDOR') roomId.value = filteredRooms.value[0]?.id || ''; logPage.value = 1; loadHistory() })
watch(building, () => { floor.value = '' })

function openModal(action, asset = null) {
  receiptSearch.value = ''
  error.value = ''; success.value = ''; selectedAsset.value = asset
  Object.assign(form, {
    name: asset?.name || '', category: asset?.category || 'Khác', quantity: asset?.quantity || 1, trackingMode: asset?.trackingMode || 'BULK', assetCode: '',
    condition: Object.keys(conditions).find(c => c !== asset?.condition) || 'HONG', note: '', actualCount: asset?.quantity || 0,
    targetRoomId: roomId.value, catalogId: action === 'RECEIPT' ? String(asset?.id || '') : '', stockId: '', enabled: asset?.enabled ?? true
  })
  if (action === 'COUNT' && asset?.trackingMode === 'INDIVIDUAL') form.actualCount = 0
  modal.value = action
}
const modalError = ref('')
async function submit() {
  if (busy.value) return
  busy.value = true; modalError.value = ''; error.value = ''; success.value = ''
  try {
    const asset = selectedAsset.value
    let path, payload, method = 'post'
    if (modal.value === 'CATALOG_CREATE' || modal.value === 'CATALOG_EDIT') {
      path = '/admin/assets/catalogs' + (modal.value === 'CATALOG_EDIT' ? `/${asset.id}` : ''); method = modal.value === 'CATALOG_EDIT' ? 'patch' : 'post'
      payload = { name: form.name, category: form.category, trackingMode: form.trackingMode, enabled: form.enabled, version: asset?.version || 1 }
    } else if (modal.value === 'CATALOG_DELETE') {
      path = `/admin/assets/catalogs/${asset.id}?version=${asset.version}`; method = 'delete'
    } else if (modal.value === 'ADD_ROOM') {
      if (!selectedStock.value) throw new Error('Chọn thiết bị trong kho.')
      path = `/admin/assets/rooms/${roomId.value}/equipment`
      payload = { equipmentId: selectedStock.value.id, quantity: Number(form.quantity), version: selectedStock.value.version, note: form.note }
    } else if (modal.value === 'ROOM_QUANTITY') {
      path = `/admin/assets/${asset.id}/room-quantity`
      payload = { actualCount: Number(form.actualCount), version: asset.version, note: form.note }
    } else if (modal.value === 'RECEIPT') {
      const catalog = selectedReceiptCatalog.value
      if (!catalog) throw new Error('Chọn danh mục thiết bị.')
      path = '/admin/assets/receipts'
      payload = { catalogId: catalog.id, name: catalog.name, category: catalog.category, quantity: catalog.trackingMode === 'INDIVIDUAL' ? 1 : Number(form.quantity), trackingMode: catalog.trackingMode, assetCode: catalog.trackingMode === 'INDIVIDUAL' ? form.assetCode : null, note: form.note }
    } else if (modal.value === 'CONDITION') {
      path = `/admin/assets/${asset.id}/condition`; method = 'patch'
      payload = { affectedCount: Number(form.quantity), version: asset.version, condition: form.condition, note: form.note }
    } else if (modal.value === 'COUNT') {
      path = `/admin/assets/${asset.id}/count`
      payload = { actualCount: Number(form.actualCount), version: asset.version, note: form.note }
    } else {
      path = `/admin/assets/${asset.id}/move`
      payload = { action: modal.value, quantity: Number(form.quantity), version: asset.version, targetRoomId: modal.value === 'RETURN' ? null : form.targetRoomId, note: form.note }
    }
    await api[method](path, payload)
    success.value = 'Đã lưu thay đổi và lịch sử tài sản.'; modal.value = null
    await refresh(); await loadHistory()
  } catch (err) { modalError.value = err.message || 'Không lưu được thay đổi.' }
  finally { busy.value = false }
}
watch(modal, () => { modalError.value = '' })

const chartNodeId = ref('')
const metric = ref('temperature')
const samples = ref([])
const telemetryLoading = ref(false)
const historyHours = ref('24')
let telemetryRequestId = 0
async function loadTelemetry() {
  const sequence = ++telemetryRequestId
  if (!chartNodeId.value) { samples.value = []; telemetryLoading.value = false; return }
  telemetryLoading.value = true
  try {
    const data = await api.get(`/admin/assets/nodes/${chartNodeId.value}/history?hours=${historyHours.value}`)
    if (sequence === telemetryRequestId) samples.value = data.samples
  } catch (err) { if (sequence === telemetryRequestId) error.value = err.message }
  finally { if (sequence === telemetryRequestId) telemetryLoading.value = false }
}
watch([chartNodeId, historyHours], loadTelemetry)
watch(visibleNodes, ns => { if (!ns.some(n => String(n.id) === chartNodeId.value)) chartNodeId.value = String(ns[0]?.id || '') })
watch(roomId, () => { powerStates.value = {}; loadPower() })
const chartValues = computed(() => samples.value.map(s => ({ time: s.measuredAt, reading: s.readings.find(r => r.metric === metric.value && r.quality !== 'BAD') })).filter(s => s.reading && Number.isFinite(s.reading.value)))
const chartRange = computed(() => {
  const values = chartValues.value.map(s => s.reading.value)
  const min = Math.min(...values), max = Math.max(...values)
  return { min: Number.isFinite(min) ? min : 0, max: Number.isFinite(max) ? max : 1, span: Math.max(1, max - min) }
})
const telemetryPoints = computed(() => chartValues.value.map((s, i, all) => ({
  ...s,
  x: all.length === 1 ? 400 : 8 + i / (all.length - 1) * 784,
  y: 172 - (s.reading.value - chartRange.value.min) / chartRange.value.span * 144
})))
const telemetryPath = computed(() => telemetryPoints.value.map((p, i) => `${i ? 'L' : 'M'}${p.x},${p.y}`).join(' '))
onMounted(async () => { await refresh(); await loadHistory(); refreshTimer = setInterval(() => { if (!busy.value && !modal.value && !stockCatalogId.value) { refresh(true); if (tab.value === 'iot') loadTelemetry() } }, 30000) })
onUnmounted(() => { clearInterval(refreshTimer); requestId++; logRequestId++; telemetryRequestId++ })
</script>

<template>
  <AdminLayout>
    <AppModal v-if="resolvingReport" title="Xử lý báo cáo hỏng hóc" :busy="busy" @close="resolvingReport = null">
      <form id="resolve-report-form" @submit.prevent="resolveDamageReport"><p class="mb-3 text-sm">{{ resolvingReport.equipmentName }} · {{ roomName(resolvingReport.roomId) }}</p><label class="block text-sm font-semibold">Kết quả xử lý<textarea v-model="resolutionNote" required minlength="3" maxlength="1000" rows="4" class="modal-field mt-2 w-full" /></label><p v-if="error" class="mt-3 text-sm text-red-600">{{ error }}</p></form>
      <template #footer><button class="modal-cancel" :disabled="busy" @click="resolvingReport = null">Hủy</button><button form="resolve-report-form" type="submit" class="modal-primary" :disabled="busy">{{ busy ? 'Đang lưu...' : 'Xác nhận đã xử lý' }}</button></template>
    </AppModal>
    <div class="w-full iot-workspace" :class="{ 'assets-workspace': tab === 'assets' || tab === 'warehouse' }">
      <header
        class="sticky top-0 z-40 flex flex-col gap-4 border-b border-slate-200/60 bg-mist/95 px-4 pt-6 pb-4 shadow-sm backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8 xl:px-12">
        <AdminPageTitle eyebrow="Tài sản & vận hành phòng" title="Quản lý tài sản" />
        <div class="flex gap-3">
          <button :disabled="loading || busy" @click="refresh()"
            class="h-10 rounded-xl border border-slate-200 bg-white px-4 text-xs font-bold text-slate-600 shadow-sm disabled:opacity-50">Làm
            mới</button>
          <button v-if="tab === 'warehouse'" @click="openModal('CATALOG_CREATE')"
            class="h-10 rounded-xl bg-brand px-5 text-xs font-bold text-white shadow-sm">+ Thêm thiết bị</button>
        </div>
      </header>
      <div class="px-4 pt-5 pb-24 sm:px-6 sm:pb-10 lg:px-8 xl:px-12">
        <p v-if="error" role="alert" class="mb-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{{
          error }}</p>
        <p v-if="success" role="status"
          class="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{{ success }}</p>
        <div class="mb-5 flex flex-wrap gap-1 rounded-xl border border-blue-100 bg-blue-50 p-1 w-fit" role="tablist"
          aria-label="Quản lý tài sản">
          <button v-for="item in tabs" :key="item.id" role="tab" :aria-selected="tab === item.id" @click="tab = item.id"
            :class="tab === item.id ? 'bg-white text-brand shadow-sm' : 'text-slate-500 hover:text-brand'"
            class="min-h-10 rounded-lg px-4 text-sm font-semibold">{{ item.name }}</button>
        </div>
        <section v-if="tab === 'iot'" class="iot-overview" aria-label="Thống kê node tổng quát">
          <div class="iot-overview-heading">
            <div>
              <h2 class="text-sm font-semibold text-ink">Tổng quan kết nối</h2>
            </div>
            <p class="text-xs text-slate-500">{{ nodeStatisticsScope }}</p>
          </div>
          <div class="iot-overview-detail">
            <div class="iot-status-grid">
              <button v-for="segment in nodeSegments" :key="segment.key" type="button"
                class="iot-status-tile" :aria-pressed="nodeFilter === segment.key"
                @click="nodeFilter = nodeFilter === segment.key ? '' : segment.key">
                <span class="iot-status-label"><i :style="{ background: segment.color }" aria-hidden="true"></i>{{ segment.label }}</span>
                <div class="flex items-baseline gap-2">
                  <strong :style="{ color: segment.color }">{{ segment.count }}</strong>
                  <span class="text-xs text-slate-500">{{ segment.unit }}</span>
                  <span class="ml-auto text-slate-400" aria-hidden="true">↗</span>
                </div>
              </button>
            </div>
          </div>
        </section>
        <section v-if="tab === 'assets'" class="iot-overview" aria-label="Thống kê tài sản tổng quát">
          <div class="iot-overview-heading">
            <h2 class="text-sm font-semibold text-ink">Tổng quan tài sản</h2>
            <p class="text-xs text-slate-500">{{ nodeStatisticsScope }}</p>
          </div>
          <div class="asset-overview-layout">
            <div class="asset-pie-panel">
              <div class="asset-pie" :style="assetPieStyle" role="img" :aria-label="assetOverview.map(item => `${item.label}: ${item.value}`).join(', ')"><div><strong>{{ assetOverview[0].value }}</strong><span>tài sản</span></div></div>
              <div class="space-y-3"><div v-for="(item, i) in assetOverview.slice(1)" :key="item.label" class="flex items-center gap-2 text-sm"><span class="size-2.5 rounded-full" :style="{ background: assetPieColors[i] }"></span><span class="text-slate-500">{{ item.label }}</span><strong class="ml-auto pl-4">{{ item.value }}</strong></div></div>
            </div>
            <div class="damage-summary-grid"><button v-for="card in reportCards" :key="card.label" @click="reportFilter = card.key" :aria-pressed="reportFilter === card.key" class="iot-status-tile text-left" :class="{ 'ring-2 ring-brand': reportFilter === card.key }"><p class="iot-status-label">{{ card.label }}</p><strong :class="card.key === 'PENDING' ? 'text-red-600' : card.key === 'RESOLVED' ? 'text-emerald-600' : 'text-ink'">{{ card.count }}</strong><p class="mt-2 text-xs text-slate-500">Báo cáo hỏng hóc</p></button></div>
          </div>
        </section>
        <div class="grid items-start gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">
          <aside v-if="tab !== 'warehouse'"
            class="overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm iot-room-picker">
            <div class="space-y-3 border-b border-blue-50 p-4">
              <h2 class="text-sm font-bold text-ink">Chọn phòng / tủ hành lang</h2>
              <input v-model="roomSearch" aria-label="Tìm phòng" placeholder="Tìm tên phòng..."
                class="h-11 w-full rounded-xl border border-blue-100 px-3 text-sm outline-none focus:ring-2 focus:ring-brand" />
              <select v-model="building" aria-label="Tòa nhà"
                class="h-11 w-full rounded-xl border border-blue-100 px-3 text-sm">
                <option value="">Tất cả tòa nhà</option>
                <option v-for="[id, name] in buildings" :key="id" :value="id">{{ name }}</option>
              </select>
              <select v-model="floor" aria-label="Tầng"
                class="h-11 w-full rounded-xl border border-blue-100 px-3 text-sm">
                <option value="">Tất cả tầng</option>
                <option v-for="f in floors" :key="f" :value="String(f)">Tầng {{ f }}</option>
              </select>
              <div v-if="tab === 'iot'"><label for="node-filter" class="mb-1 block text-xs text-slate-500">Tình trạng
                  node</label><select id="node-filter" v-model="nodeFilter"
                  class="h-11 w-full rounded-xl border border-blue-100 bg-white px-3 text-sm">
                  <option value="">Tất cả tình trạng</option>
                  <option value="ACTIVE">Đang hoạt động</option>
                  <option value="ONLINE">Trực tuyến</option>
                  <option value="OFFLINE">Ngoại tuyến</option>
                  <option value="DISABLED">Đang bảo trì</option>
                </select></div>
            </div>
            <div class="max-h-80 overflow-y-auto xl:max-h-[55dvh]">
              <button v-for="r in roomPageItems" :key="r.id" @click="roomId = r.id"
                :class="roomId === r.id ? 'bg-blue-50 text-brand' : 'text-ink hover:bg-slate-50'"
                class="block w-full border-b border-blue-50 px-4 py-3 text-left">
                <span class="flex items-center justify-between gap-2">
                  <span class="text-sm font-semibold">{{ r.name }}<span v-if="tab === 'assets' && damageReports.some(report => report.roomId === r.id && report.status === 'PENDING')" class="ml-2 text-xs text-red-600">● Báo hỏng</span></span>
                  <span v-if="tab === 'iot'" class="iot-room-badge" :class="{ 'is-online': roomConnections[r.id]?.online }">
                    <span aria-hidden="true">●</span> {{ roomConnections[r.id]?.online || 0 }}/{{ roomConnections[r.id]?.total || 0 }} online
                  </span>
                </span><span
                  class="mt-1 block text-xs text-slate-500">Tầng {{ r.floor }} · {{ countInRoom(r.id) }} tài sản</span>
              </button>
              <p v-if="!filteredRooms.length" class="p-4 text-sm text-slate-500">
                {{ loading ? 'Đang tải...' : 'Không có phòng phù hợp.' }}
              </p>
            </div>
            <TablePagination v-model:page="roomPage" :total-items="roomTotal" label="phòng" compact />
          </aside>
          <section class="panel-stack flex min-w-0 flex-col gap-5" :class="tab === 'warehouse' ? 'xl:col-span-2' : ''">
            <div v-if="tab === 'iot'" class="iot-room-heading">
              <div class="iot-room-symbol" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 21V3h16v18M2 21h20M9 21v-6h6v6M8 7h2m4 0h2M8 11h2m4 0h2" /></svg>
              </div>
              <div class="min-w-0 flex-1">
                <p class="iot-eyebrow">PHÒNG ĐANG XEM</p>
                <h2 class="text-xl font-bold text-ink">{{ selectedRoom?.name || 'Chưa chọn phòng' }}</h2>
                <p v-if="selectedRoom" class="mt-1 text-xs text-slate-500">Tầng {{ selectedRoom.floor }} · {{ selectedRoom.building }}</p>
              </div>
              <div class="ml-auto flex flex-wrap items-center justify-end gap-3">
                <span v-if="selectedNodes.length" class="text-xs text-slate-500">Lần nhận cuối: {{ dateTime(roomLastSeenAt) }}</span>
                <span class="iot-room-summary">{{ selectedNodes.filter(n => n.status === 'ONLINE').length }} / {{ selectedNodes.length }} node trực tuyến</span>
              </div>
            </div>
            <div v-else-if="tab !== 'warehouse'" class="iot-room-heading">
              <div class="iot-room-symbol" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 21V3h16v18M2 21h20M9 21v-6h6v6M8 7h2m4 0h2M8 11h2m4 0h2" /></svg>
              </div>
              <div class="min-w-0 flex-1">
                <p class="iot-eyebrow">PHÒNG ĐANG XEM</p>
                <h2 class="text-xl font-bold text-ink">{{ selectedRoom?.name || 'Chưa chọn phòng' }}</h2>
                <p v-if="selectedRoom" class="mt-1 text-xs text-slate-500">Tầng {{ selectedRoom.floor }} · {{ selectedRoom.building }}</p>
              </div>
              <div class="asset-room-stats">
                <div>
                  <p class="text-xs text-slate-500">Tài sản tại phòng</p><b class="text-xl text-ink">{{
                    roomInventory.reduce((sum, e) => sum + e.quantity, 0)}}</b>
                </div>
                <div>
                  <p class="text-xs text-slate-500">Cần theo dõi</p><b class="text-xl text-amber-600">{{ needsAttention
                  }}</b>
                </div>
                <div>
                  <p class="text-xs text-slate-500">Node online / tổng</p><b class="text-xl text-brand">{{
                    selectedNodes.filter(n => n.status === 'ONLINE').length}} / {{ selectedNodes.length }}</b>
                </div>
                <div>
                  <p class="text-xs text-slate-500">Kho khả dụng</p><b class="text-xl text-emerald-600">{{
                    warehouseCount }}</b>
                </div>
              </div>
            </div>

            <template v-if="tab === 'iot'">

              <div v-if="selectedNodes.length && !visibleNodes.length"
                class="rounded-2xl border border-blue-100 bg-white p-6 text-sm text-slate-500">Không có node phù hợp với
                bộ lọc.</div>
              <div v-if="!selectedNodes.length"
                class="rounded-2xl border border-blue-100 bg-white p-6 text-sm text-slate-500">Phòng chưa cấu hình node
                IoT.</div>
              <div v-for="node in visibleNodes" :key="node.id"
                class="iot-node-card">
                <div class="flex flex-wrap items-start justify-between gap-4">
                    <div class="flex shrink-0 items-center gap-3">
                      <select
                        :id="`node-status-${node.id}`" :value="node.status === 'DISABLED' ? 'DISABLED' : 'ACTIVE'"
                        :disabled="busy" @change="saveNode(node, $event)"
                        class="h-10 w-40 rounded-xl border border-blue-100 bg-white px-3 text-[14px]! text-ink outline-none focus:ring-2 focus:ring-brand disabled:opacity-50">
                        <option value="ACTIVE">Đang hoạt động</option>
                        <option value="DISABLED">Đang bảo trì</option>
                      </select>
                    </div>
                  <div class="ml-auto flex min-w-0 flex-col items-end gap-2 text-right">
                    <span
                      :class="node.status === 'DISABLED' ? 'bg-amber-50 text-amber-700' : node.status === 'ONLINE' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'"
                      class="rounded-lg px-3 py-1 text-xs font-bold">{{ node.status === 'DISABLED' ? 'Bảo trì' :
                        node.status === 'ONLINE' ? 'Trực tuyến' : 'Ngoại tuyến' }}</span>
                  </div>
                </div>
                <div class="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-slate-100 pt-4 text-xs text-slate-600">
                  <h4 class="mr-auto text-sm font-semibold text-ink">Thông số thiết bị</h4>
                  <span class="text-emerald-700">● Ổn định</span>
                  <span class="text-amber-700">● Cảnh báo</span>
                  <span class="text-red-700">● Cần xử lý ngay</span>
                </div>
                <div class="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
                  <div v-for="m in metrics" :key="m.key" class="iot-metric-card rounded-xl border p-3"
                    :class="metricState(node, m.key).classes">
                    <div class="flex items-center justify-between gap-2">
                      <p class="text-xs text-slate-500">{{ m.name }}</p>
                      <svg class="iot-metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="metricIcons[m.key]" /></svg>
                    </div>
                    <p class="mt-3 text-2xl font-bold tracking-tight text-ink">{{node.readings.find(r => r.metric === m.key)?.value ??
                      '—'}} <span class="text-xs font-normal text-slate-500">{{ m.unit }}</span></p>
                    <p class="mt-2 text-xs font-semibold">● {{ metricState(node, m.key).label }}</p>
                    <p v-if="node.readings.find(r => r.metric === m.key)?.quality !== 'GOOD'"
                      class="mt-1 text-xs text-slate-500">
                      {{node.readings.find(r => r.metric === m.key)?.quality || 'Chưa có dữ liệu'}}
                    </p>
                  </div>
                </div>
                <section class="iot-analysis mt-4 rounded-xl border border-blue-100 bg-blue-50/40 p-4 text-sm"
                  aria-label="Kết quả phân tích AI">
                  <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <h4 class="font-semibold text-ink">Kết quả phân tích AI</h4><span
                      class="rounded-lg bg-white px-2 py-1 text-xs text-slate-500">Nhận định theo quy tắc</span>
                  </div>
                  <p class="font-semibold">Dòng điện tổng phòng · {{ borrowingLabel(node) }}</p>
                  <p class="mt-1"
                    :class="powerStates[node.id]?.state === 'OUT_OF_SCHEDULE' ? 'text-amber-700' : 'text-slate-600'">{{
                      powerLabels[powerStates[node.id]?.state] || powerLabels.UNKNOWN }}</p>
                  <p v-if="powerStates[node.id] && !powerStates[node.id].isFresh && powerStates[node.id].currentAmperes != null"
                    class="mt-1 text-xs text-slate-500">Giá trị cuối nhận được: {{ powerStates[node.id].currentAmperes
                    }} A · {{ dateTime(powerStates[node.id].measuredAt) }}</p>
                  <p class="mt-1 text-xs text-slate-500">Mốc tiêu thụ 1A; cảnh báo ngoài lịch sau 5 phút đo liên tục.
                    Chưa xác định bật/tắt từng thiết bị hoặc có người trong phòng.</p>
                </section>
              </div>
              <div v-if="visibleNodes.length" class="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm">
                <div class="mb-4 flex flex-wrap items-center gap-3">
                  <h3 class="mr-auto text-sm font-bold text-ink">Lịch sử cảm biến</h3><select v-model="chartNodeId"
                    aria-label="Chọn node" class="h-10 rounded-xl border border-blue-100 px-3 text-sm">
                    <option v-for="n in visibleNodes" :key="n.id" :value="String(n.id)">{{ nodeDisplayCode(n) }}
                    </option>
                  </select><select v-model="metric" aria-label="Thông số"
                    class="h-10 rounded-xl border border-blue-100 px-3 text-sm">
                    <option v-for="m in metrics" :key="m.key" :value="m.key">{{ m.name }}</option>
                  </select><select v-model="historyHours" aria-label="Khoảng xem"
                    class="h-10 rounded-xl border border-blue-100 px-3 text-sm">
                    <option value="24">24 giờ</option>
                    <option value="168">7 ngày</option>
                    <option value="720">30 ngày</option>
                  </select>
                </div>
                <svg v-if="telemetryPoints.length" viewBox="0 0 800 200" preserveAspectRatio="none" class="h-48 w-full"
                  role="img" :aria-label="`Lịch sử ${metric}`">
                  <path v-for="y in [28, 76, 124, 172]" :key="y" :d="`M8 ${y} H792`" stroke="#e2e8f0" stroke-dasharray="4 5" />
                  <path v-if="telemetryPoints.length > 1" :d="`${telemetryPath} L${telemetryPoints.at(-1).x},184 L${telemetryPoints[0].x},184 Z`" fill="var(--color-brand)" opacity="0.07" />
                  <path :d="telemetryPath" fill="none" stroke="var(--color-brand)" stroke-width="2" />
                  <circle v-for="p in telemetryPoints" :key="p.time" :cx="p.x" :cy="p.y" r="3"
                    fill="var(--color-brand)">
                    <title>{{ dateTime(p.time) }}: {{ p.reading.value }} {{ p.reading.unit }}</title>
                  </circle>
                </svg>
                <p v-else class="py-10 text-center text-sm text-slate-400">{{ telemetryLoading ? 'Đang tải...' :
                  uiText.noTelemetry }}</p>
                <div v-if="telemetryPoints.length" class="mt-2 flex justify-between gap-3 text-[10px] text-slate-500">
                  <span>{{ dateTime(telemetryPoints[0].time) }}</span><span>{{ dateTime(telemetryPoints.at(-1).time)
                  }}</span>
                </div>
              </div>
            </template>

            <template v-else-if="tab === 'warehouse'">
              <section class="iot-overview" aria-label="Tổng quan kho thiết bị">
                <div class="iot-overview-heading">
                  <h2 class="text-sm font-semibold text-ink">Tổng quan kho thiết bị</h2>
                  <p class="text-xs text-slate-500">Tất cả phòng</p>
                </div>
                <div class="asset-summary-grid">
                  <div v-for="item in warehouseSummary" :key="item.label"
                    class="iot-status-tile">
                    <p class="iot-status-label"><span :class="item.color" aria-hidden="true">●</span>{{ item.label }}</p>
                    <strong :class="item.color">{{ item.value }}</strong>
                  </div>
                </div>
              </section>
              <div class="asset-table-card">
                <div class="p-5">
                <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <h3 class="text-sm font-semibold text-ink">Danh mục thiết bị</h3>
                </div>
                <div class="flex flex-wrap items-center gap-3"><input v-model="search" aria-label="Tìm thiết bị trong kho"
                    placeholder="Tìm tên, phân loại thiết bị..."
                    class="h-11 w-full min-w-0 rounded-xl border border-blue-100 px-4 text-sm outline-none focus:ring-2 focus:ring-brand sm:w-0 sm:flex-1" /><select
                    v-model="catalogFilter" aria-label="Phân loại thiết bị"
                    class="h-11 rounded-xl border border-blue-100 px-3 text-sm">
                    <option value="">Tất cả phân loại</option>
                    <option v-for="category in [...new Set(catalogs.map(c => c.category))]" :key="category">{{ category
                    }}
                    </option>
                  </select><select v-model="catalogEnabledFilter" aria-label="Trạng thái danh mục"
                    class="h-11 rounded-xl border border-blue-100 px-3 text-sm">
                    <option value="">Tất cả danh mục</option>
                    <option value="true">Đang sử dụng</option>
                    <option value="false">Ngừng sử dụng</option>
                  </select>
                  <button @click="openModal('RECEIPT')"
                    class="h-11 shrink-0 whitespace-nowrap rounded-xl bg-brand px-4 text-xs font-semibold text-white">+ Nhập kho</button>
                </div>
                </div>
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead class="border-b border-blue-50 bg-blue-50/60 text-xs uppercase text-slate-500">
                      <tr>
                        <th class="px-5 py-4 text-left">Thiết bị / phân loại</th>
                        <th class="px-5 py-4 text-left">Tổng</th>
                        <th class="px-5 py-4 text-left">Đã cấp</th>
                        <th class="px-5 py-4 text-left">Trong kho</th>
                        <th class="px-5 py-4 text-left">Khả dụng</th>
                        <th class="px-5 py-4 text-left">Trạng thái</th>
                        <th class="px-5 py-4 text-right">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="c in catalogPageItems" :key="c.id" class="border-b border-blue-50">
                        <td class="px-5 py-4">
                          <p class="font-semibold text-ink">{{ c.name }}</p>
                          <p class="mt-1 text-xs text-slate-500">{{ c.category }} · {{ c.trackingMode === 'BULK' ?
                            uiText.bulkTracking : 'Theo từng chiếc' }}</p>
                        </td>
                        <td class="px-5 py-4 font-semibold">{{ c.total }}</td>
                        <td class="px-5 py-4">{{ c.allocated }}</td>
                        <td class="px-5 py-4">{{ c.inStock }}<div class="mt-1 flex flex-wrap gap-1"><span
                              v-for="(label, key) in conditions" :key="key"
                              v-show="equipment.some(e => e.catalogId === c.id && !e.roomId && e.condition === key)"
                              class="rounded bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-500">{{ label }}: {{
                                equipment.filter(e => e.catalogId === c.id && !e.roomId &&
                                  e.condition === key).reduce((sum, e) => sum + e.quantity, 0)}}</span></div>
                        </td>
                        <td class="px-5 py-4 text-emerald-700">{{ c.available }}</td>
                        <td class="px-5 py-4 text-xs">
                          <span class="inline-flex whitespace-nowrap rounded-lg px-2.5 py-1 text-xs font-semibold"
                            :class="c.enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'">{{ c.enabled ? 'Đang sử dụng' : 'Ngừng sử dụng' }}</span>
                        </td>
                        <td class="px-5 py-4">
                          <div class="flex flex-wrap justify-end gap-2"><button @click="showWarehouseDetails(c.id)"
                              class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200">Quản
                              lý tồn kho</button><button v-if="c.enabled" @click="openModal('RECEIPT', c)"
                              class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200">Nhập
                              thêm</button><button @click="openModal('CATALOG_EDIT', c)"
                              class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200">Sửa</button><button
                              @click="openModal('CATALOG_DELETE', c)"
                              class="asset-action-danger rounded-lg bg-red-50 px-2.5 py-1 text-xs font-bold text-red-600 hover:bg-red-600 hover:text-white active:scale-95 transition border border-red-200">Xóa</button>
                          </div>
                        </td>
                      </tr>
                      <tr v-if="!catalogPageItems.length">
                        <td colspan="7" class="px-5 py-10 text-center text-slate-400">Chưa có danh mục phù hợp.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <TablePagination v-model:page="catalogPage" :total-items="catalogTotal" label="danh mục" />
              </div>
              <div class="asset-table-card">
                <div class="flex items-center justify-between border-b border-blue-50 p-5">
                  <h3 class="text-sm font-semibold text-ink">Lịch sử kho và tài sản</h3><button @click="loadHistory"
                    class="text-xs font-semibold text-brand">Làm mới</button>
                </div>
                <div v-for="log in logs" :key="log.id" class="border-b border-blue-50 px-5 py-3 text-xs text-slate-500">
                  <p>{{ dateTime(log.createdAt) }} · {{ log.actor }} · {{ actions[log.action.replace('ASSET_', '')] ||
                    log.action }}</p>
                  <p class="mt-1 font-semibold text-ink">{{ log.detail.name }} · {{ log.detail.quantity }}</p>
                  <p>{{ log.detail.note }}</p>
                </div>
                <p v-if="!logs.length" class="px-5 py-8 text-center text-xs text-slate-400">Chưa có lịch sử.</p>
                <TablePagination v-model:page="logPage" :total-items="logTotal" label="sự kiện" />
              </div>
            </template>

            <template v-else-if="tab === 'assets'">
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
              </section>
              <div class="asset-table-card">
                <div class="p-5">
                <h3 class="mb-4 text-sm font-semibold text-ink">Tài sản tại phòng</h3>
                <div class="flex flex-wrap items-center gap-3">
                  <input v-model="search" aria-label="Tìm tài sản" placeholder="Tìm tên, loại, mã tài sản..."
                    class="h-11 w-full min-w-0 rounded-xl border border-blue-100 bg-white px-4 text-sm outline-none focus:ring-2 focus:ring-brand sm:w-0 sm:flex-1" />
                  <select v-model="conditionFilter" aria-label="Tình trạng"
                    class="h-11 shrink-0 rounded-xl border border-blue-100 bg-white px-3 text-sm">
                    <option value="">Tất cả tình trạng</option>
                    <option v-for="(name, key) in conditions" :key="key" :value="key">{{ name }}</option>
                  </select>
                  <button :disabled="!roomId || busy" @click="openModal('ADD_ROOM')"
                    class="h-11 shrink-0 whitespace-nowrap rounded-xl bg-brand px-4 text-xs font-semibold text-white disabled:opacity-50">+
                    Thêm thiết bị</button>
                </div>
                </div>
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="border-b border-blue-50 bg-blue-50/60">
                        <th class="px-5 py-4 text-left text-xs font-bold uppercase text-slate-500">Tài sản</th>
                        <th class="px-5 py-4 text-left text-xs font-bold uppercase text-slate-500">Số lượng</th>
                        <th class="px-5 py-4 text-left text-xs font-bold uppercase text-slate-500">Tình trạng</th>
                        <th class="px-5 py-4 text-left text-xs font-bold uppercase text-slate-500">Ghi chú</th>
                        <th class="px-5 py-4 text-right text-xs font-bold uppercase text-slate-500">Thao tác</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="asset in pageItems" :key="asset.id"
                        class="border-b border-blue-50 hover:bg-blue-50/30">
                        <td class="px-5 py-4">
                          <p class="font-semibold text-ink">{{ asset.name }}</p>
                          <p class="mt-1 text-xs text-slate-500">{{ asset.assetCode || asset.category }} · {{
                            asset.usageScope === 'CABINET' ? 'Bộ thiết bị tủ' : roomName(asset.roomId) }}</p>
                        </td>
                        <td class="px-5 py-4 font-semibold text-ink">{{ asset.quantity }}<p
                            class="mt-1 text-xs font-normal text-slate-500">Kho khả dụng: {{
                              equipment.filter(e => e.catalogId === asset.catalogId && !e.roomId &&
                                e.condition === 'TOT').reduce((sum, e) => sum + e.quantity, 0)}}</p>
                        </td>
                        <td class="px-5 py-4"><span
                            :class="assetConditionClasses[asset.condition] || 'bg-slate-100 text-slate-600'"
                            class="inline-flex whitespace-nowrap rounded-lg px-2.5 py-1 text-xs font-semibold">{{
                              conditions[asset.condition] || asset.condition }}</span></td>
                        <td class="max-w-xs px-5 py-4 text-xs text-slate-500">{{ asset.note || '—' }}</td>
                        <td class="px-5 py-4">
                          <div class="flex flex-wrap justify-end gap-2">
                            <button @click="openModal('ROOM_QUANTITY', asset)"
                              class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200">Thay
                              đổi số lượng</button>
                            <button @click="openModal('CONDITION', asset)"
                              class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200">Báo
                              / đổi tình trạng</button>
                          </div>
                        </td>
                      </tr>
                      <tr v-if="!pageItems.length">
                        <td colspan="5" class="px-5 py-12 text-center text-slate-400">{{ loading ? 'Đang tải tài sản...'
                          : 'Chưa có tài sản phù hợp. Chọn Thêm thiết bị để lấy thiết bị từ kho vào phòng.' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <TablePagination v-model:page="page" :total-items="totalItems" :disabled="loading || busy"
                  label="nhóm / tài sản" />
              </div>
              <div class="asset-table-card">
                <div class="flex flex-wrap items-center justify-between gap-3 border-b border-blue-50 px-5 py-4">
                  <h3 class="text-sm font-bold text-ink">Lịch sử tài sản</h3><button @click="loadHistory"
                    class="text-xs font-semibold text-brand">Làm mới lịch sử</button>
                </div>
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead class="bg-blue-50/60 text-xs text-slate-500">
                      <tr>
                        <th class="px-5 py-3 text-left">Thời gian / người cập nhật</th>
                        <th class="px-5 py-3 text-left">Nghiệp vụ</th>
                        <th class="px-5 py-3 text-left">Nội dung</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="log in logs" :key="log.id" class="border-t border-blue-50">
                        <td class="px-5 py-3 text-xs text-slate-500">{{ dateTime(log.createdAt) }}<p
                            class="mt-1 text-ink">{{ log.actor }}</p>
                        </td>
                        <td class="px-5 py-3 text-xs text-brand">{{ actions[log.action.replace('ASSET_', '')] ||
                          log.action }}</td>
                        <td class="px-5 py-3 text-xs text-slate-500"><b class="text-ink">{{ log.detail.name }}</b> · {{
                          log.detail.quantity }}<p v-if="log.detail.fromRoomId !== log.detail.toRoomId">{{
                            roomName(log.detail.fromRoomId) }} → {{ roomName(log.detail.toRoomId) }}</p>
                          <p v-if="log.action === 'ASSET_CONDITION'">{{ conditions[log.detail.oldCondition] }} → {{
                            conditions[log.detail.condition] }}</p>
                          <p v-if="log.action === 'ASSET_COUNT'">{{ log.detail.before }} → {{ log.detail.after }}</p>
                          <p>{{ log.detail.note }}</p>
                        </td>
                      </tr>
                      <tr v-if="!logs.length">
                        <td colspan="3" class="px-5 py-8 text-center text-xs text-slate-400">Chưa có lịch sử cập nhật
                          cho phòng này.</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <TablePagination v-model:page="logPage" :total-items="logTotal" label="sự kiện" />
              </div>
            </template>
          </section>
        </div>
      </div>
    </div>
    <AppModal v-if="stockCatalogId" :title="`Tồn kho · ${catalogs.find(c => c.id === stockCatalogId)?.name || ''}`"
      size="lg" :busy="busy" @close="stockCatalogId = null">
      <div class="mb-4"><label for="stock-condition" class="modal-label">Tình trạng</label><select id="stock-condition"
          v-model="stockConditionFilter" class="modal-field">
          <option value="">Tất cả tình trạng</option>
          <option v-for="(name, key) in conditions" :key="key" :value="key">{{ name }}</option>
        </select></div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-blue-50/60 text-xs uppercase text-slate-500">
            <tr>
              <th class="px-5 py-3 text-left">Thiết bị</th>
              <th class="px-5 py-3 text-left">Số lượng</th>
              <th class="px-5 py-3 text-left">Tình trạng</th>
              <th class="px-5 py-3 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="e in stockPageItems" :key="e.id" class="border-t border-blue-50">
              <td class="px-5 py-4 font-semibold">{{ e.name }}<p class="mt-1 text-xs font-normal text-slate-500">{{
                e.assetCode || e.category }}</p>
              </td>
              <td class="px-5 py-4">{{ e.quantity }}</td>
              <td class="px-5 py-4 text-xs">{{ conditions[e.condition] }}</td>
              <td class="px-5 py-4">
                <div class="flex flex-wrap justify-end gap-3"><button @click="openModal('COUNT', e)"
                    :class="e.trackingMode === 'BULK' ? 'rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200' : 'rounded-lg bg-red-50 px-2.5 py-1 text-xs font-bold text-red-600 hover:bg-red-600 hover:text-white active:scale-95 transition border border-red-200'">{{
                      e.trackingMode === 'BULK' ? 'Thay đổi số lượng' : 'Xóa khỏi kho' }}</button><button
                    @click="openModal('CONDITION', e)"
                    class="rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200">Đổi
                    tình trạng</button></div>
              </td>
            </tr>
            <tr v-if="!stockPageItems.length">
              <td colspan="4" class="px-5 py-10 text-center text-slate-400">Chưa có thiết bị trong kho phù hợp. Nhập kho
                để
                bổ sung số lượng.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <TablePagination v-model:page="stockPage" :total-items="stockTotal" label="nhóm / thiết bị" />
      <template #footer><button @click="stockCatalogId = null" :disabled="busy"
          class="modal-cancel">Đóng</button></template>
    </AppModal>
    <AppModal v-if="modal" :title="actions[modal]" :layer="stockCatalogId ? 'nested' : 'normal'" size="md" :busy="busy"
      @close="modal = null">
      <form id="asset-operation" class="space-y-4" @submit.prevent="submit">
        <p v-if="selectedAsset && !modal.startsWith('CATALOG_')" class="rounded-xl bg-blue-50 p-3 text-sm text-ink">
          <b>{{
            selectedAsset.name }}</b> · {{ selectedAsset.quantity }} · {{ roomName(selectedAsset.roomId) }}
        </p>
        <template v-if="modal === 'CATALOG_CREATE' || modal === 'CATALOG_EDIT'">
          <div><label for="catalog-name" class="modal-label">Tên thiết bị</label><input id="catalog-name"
              v-model="form.name" required maxlength="100" class="modal-field" /></div>
          <div><label for="catalog-category" class="modal-label">Phân loại</label><input id="catalog-category"
              v-model="form.category" required maxlength="50" class="modal-field" /></div>
          <div><label for="catalog-tracking" class="modal-label">Cách quản lý</label><select id="catalog-tracking"
              v-model="form.trackingMode" :disabled="modal === 'CATALOG_EDIT'" class="modal-field">
              <option value="BULK">Theo số lượng</option>
              <option value="INDIVIDUAL">Theo từng chiếc</option>
            </select></div>
          <div><label for="catalog-enabled" class="modal-label">Trạng thái danh mục</label><select id="catalog-enabled"
              v-model="form.enabled" class="modal-field">
              <option :value="true">Đang sử dụng</option>
              <option :value="false">Ngừng sử dụng</option>
            </select></div>
        </template>
        <p v-if="modal === 'CATALOG_DELETE'" class="text-sm text-slate-600">Xóa danh mục {{ selectedAsset?.name }}? Chỉ
          được
          xóa khi không còn thiết bị trong kho hoặc tại phòng. Danh mục còn thiết bị có thể chuyển sang Ngừng sử dụng.
        </p>
        <template v-if="modal === 'RECEIPT'">
          <div><label for="receipt-search" class="modal-label">Tìm thiết bị</label><input id="receipt-search"
              v-model="receiptSearch" type="search" placeholder="Tìm tên, phân loại thiết bị..." class="modal-field" />
            <p v-if="!receiptCatalogs.length" class="mt-2 text-xs text-slate-500">Không có danh mục phù hợp.</p>
          </div>
          <div><label for="receipt-catalog" class="modal-label">Danh mục thiết bị</label><select id="receipt-catalog"
              v-model="form.catalogId" required class="modal-field">
              <option value="" disabled>Chọn danh mục</option>
              <option v-for="c in receiptCatalogs" :key="c.id" :value="String(c.id)">{{ c.name }} · {{ c.category }}
              </option>
            </select></div>
          <div v-if="selectedReceiptCatalog?.trackingMode === 'INDIVIDUAL'"><label for="asset-code"
              class="modal-label">Mã
              thiết bị duy nhất</label><input id="asset-code" v-model="form.assetCode" required maxlength="80"
              class="modal-field" />
            <p class="mt-2 text-xs text-slate-500">Mỗi lần nhập một chiếc, số lượng bằng 1.</p>
          </div>
        </template>
        <template v-if="modal === 'ADD_ROOM'">
          <div><label for="room-stock" class="modal-label">Thiết bị khả dụng trong kho</label><select id="room-stock"
              v-model="form.stockId" required class="modal-field">
              <option value="" disabled>Chọn thiết bị</option>
              <option v-for="e in availableStock" :key="e.id" :value="String(e.id)">{{ e.name }} · {{ e.assetCode ||
                e.category }} · còn {{ e.quantity }}</option>
            </select></div>
          <p v-if="!availableStock.length" class="text-sm text-amber-700">Kho chưa có thiết bị sử dụng tốt. Nhập thiết
            bị trong tab Kho thiết bị trước.</p>
          <p class="text-xs text-slate-500">Phòng nhận: {{ selectedRoom?.name }}</p>
        </template>
        <div
          v-if="['ADD_ROOM', 'CONDITION'].includes(modal) || (modal === 'RECEIPT' && selectedReceiptCatalog?.trackingMode !== 'INDIVIDUAL')">
          <label for="asset-quantity" class="modal-label">{{ modal === 'CONDITION' ? 'Số lượng chuyển tình trạng' :
            uiText.quantity
          }}</label><input id="asset-quantity" v-model.number="form.quantity" type="number" min="1"
            :max="modal === 'ADD_ROOM' ? selectedStock?.quantity || 1 : modal === 'CONDITION' ? selectedAsset?.quantity || 1 : 10000"
            required step="1" class="modal-field" />
        </div>
        <div v-if="modal === 'COUNT' || modal === 'ROOM_QUANTITY'"><label for="asset-actual" class="modal-label">Số
            lượng
            mới</label><input id="asset-actual" v-model.number="form.actualCount" type="number" min="0"
            :max="selectedAsset?.trackingMode === 'INDIVIDUAL' ? (modal === 'COUNT' ? 0 : 1) : 10000" required step="1"
            class="modal-field" />
          <p v-if="modal === 'ROOM_QUANTITY'" class="mt-2 text-xs text-slate-500">Tăng lấy thêm từ kho; giảm trả về kho,
            giữ
            nguyên tình trạng. Thiết bị riêng lẻ nhập 0 để trả về kho.</p>
        </div>
        <div v-if="modal === 'CONDITION'"><label for="asset-condition" class="modal-label">Tình trạng mới</label><select
            id="asset-condition" v-model="form.condition" required class="modal-field">
            <option v-for="(name, key) in conditions" :key="key" :value="key"
              :disabled="key === selectedAsset?.condition">
              {{
                name }}</option>
          </select></div>
        <div v-if="!modal.startsWith('CATALOG_')"><label for="asset-note" class="modal-label">{{ modal === 'RECEIPT' ?
          'Ghi chú' : 'Lý do / ghi chú (bắt buộc)' }}</label><textarea id="asset-note" v-model="form.note"
            :required="modal !== 'RECEIPT'" maxlength="255" class="modal-field" /></div>
        <p v-if="modalError" role="alert" class="text-sm text-red-600">{{ modalError }}</p>
      </form>
      <template #footer><button :disabled="busy" @click="modal = null" class="modal-cancel">Hủy</button><button
          type="submit" form="asset-operation" :disabled="busy" class="modal-primary">{{ busy ? 'Đang lưu...' :
            uiText.confirm }}</button></template>
    </AppModal>
  </AdminLayout>
</template>

<style scoped>
.iot-workspace { background: #f5f7fb; }
.iot-workspace input, .iot-workspace select, .iot-workspace button { font-size: 13px; }
.iot-overview {
  display: grid;
  gap: 14px;
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  background: white;
}
.iot-overview-heading { display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.panel-stack > .iot-overview { margin-bottom: 0; }
.iot-eyebrow { color: #64748b; font-size: 10px; font-weight: 700; letter-spacing: .12em; }
.iot-overview-detail { min-width: 0; }
.iot-status-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.iot-status-tile { display: grid; gap: 6px; padding: 12px 14px; border: 1px solid #edf1f5; border-radius: 12px; background: #f8fafc; text-align: left; transition: background .15s, border-color .15s; }
.iot-status-tile:hover, .iot-status-tile[aria-pressed="true"] { border-color: #93c5fd; background: #eff6ff; }
.iot-status-label { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #475569; }
.iot-status-label i { width: 6px; height: 6px; border-radius: 50%; }
.iot-status-tile strong { font-size: 26px; line-height: 1.1; }
.iot-room-picker { border-color: #e2e8f0; box-shadow: none; }
.iot-room-badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 6px; border-radius: 5px; background: #f1f5f9; color: #64748b; font-size: 10px; white-space: nowrap; }
.iot-room-badge.is-online { background: #ecfdf5; color: #047857; }
.iot-room-heading { display: flex; align-items: center; flex-wrap: wrap; gap: 14px; padding: 18px 20px; border: 1px solid #e2e8f0; border-radius: 16px; background: white; }
.iot-room-symbol { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 12px; background: #eff6ff; color: #0969c7; }
.iot-room-symbol svg { width: 25px; height: 25px; }
.iot-room-summary { padding: 7px 10px; border-radius: 8px; background: #f1f5f9; color: #475569; font-size: 12px; }
.iot-node-card { padding: 20px; border: 1px solid #dce4ed; border-radius: 16px; background: white; box-shadow: 0 2px 5px #102a4304; }
.iot-metric-card { min-width: 0; padding: 16px; }
.iot-metric-icon { width: 22px; height: 22px; flex-shrink: 0; opacity: .65; }
.iot-analysis { border-left: 3px solid #93c5fd; background: #f8fafc; }
.iot-workspace button:focus-visible { outline: 2px solid #0969c7; outline-offset: 3px; }
.asset-summary-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
.asset-summary-grid .iot-status-tile:hover { border-color: #edf1f5; background: #f8fafc; }
.asset-room-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; width: 100%; padding-top: 16px; margin-top: 2px; border-top: 1px solid #f1f5f9; }
.asset-room-stats > div { padding: 10px 12px; border-radius: 10px; background: #f8fafc; }
.asset-table-card { overflow: hidden; border: 1px solid #dce4ed; border-radius: 16px; background: white; box-shadow: 0 2px 5px #102a4304; }
.assets-workspace table thead { background: #f8fafc; }
.assets-workspace table thead tr { background: transparent; border-color: #e2e8f0; }
.assets-workspace table th { font-size: 11px; font-weight: 600; letter-spacing: .04em; }
.assets-workspace table tbody tr { border-color: #edf1f5; }
.assets-workspace table tbody tr:hover { background: #f8fafc; }
.assets-workspace table td button { font-weight: 500; border-color: #e2e8f0; background: white; color: #0969c7; }
.assets-workspace table td button:hover { border-color: #bfdbfe; background: #eff6ff; }
.assets-workspace table td button.asset-action-danger { border-color: #fecaca; background: #fff; color: #dc2626; }
.assets-workspace table td button.asset-action-danger:hover { border-color: #fca5a5; background: #fef2f2; }
@media (max-width: 900px) {
  .asset-summary-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .asset-summary-grid, .asset-room-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .iot-overview { padding: 16px; }
  .iot-status-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
  .iot-status-tile { padding: 10px 8px; }
  .iot-status-label { font-size: 11px; }
  .iot-node-card { padding: 16px; }
  .iot-metric-card { padding: 12px; }
}
</style>

<style scoped>
.asset-overview-layout { display: grid; grid-template-columns: minmax(320px, 1fr) minmax(0, 1.2fr); gap: 24px; align-items: center; }
.asset-pie-panel { display: flex; align-items: center; gap: 24px; }
.asset-pie { width: 160px; height: 160px; border-radius: 50%; display: grid; place-items: center; flex-shrink: 0; }
.asset-pie > div { width: 112px; height: 112px; background: white; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.asset-pie strong { font-size: 28px; } .asset-pie span { color: #64748b; font-size: 12px; }
.damage-summary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
@media (max-width: 1100px) { .asset-overview-layout { grid-template-columns: 1fr; } }
@media (max-width: 480px) { .asset-pie-panel { gap: 12px; } .asset-pie { width: 125px; height: 125px; } .asset-pie > div { width: 88px; height: 88px; } .damage-summary-grid { grid-template-columns: 1fr; } }
</style>
