from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8').replace("{ id: 'allocation', name: 'Phân bổ thiết bị' }", "{ id: 'warehouse', name: 'Kho thiết bị' }")
s=s.replace("tabs.some(t => t.id === route.query.tab) ? route.query.tab : 'iot'", "route.query.tab === 'allocation' ? 'warehouse' : tabs.some(t => t.id === route.query.tab) ? route.query.tab : 'iot'")
s=s.replace("const locationFilter = ref('warehouse')", "const catalogs = ref([])\nconst catalogFilter = ref('')\nconst catalogEnabledFilter = ref('')\nconst stockCatalogId = ref(null)")
s=s.replace("actualCount: 0 })", "actualCount: 0, catalogId: '', stockId: '', enabled: true })",1)
s=s.replace("const actions = {", "const actions = { CATALOG_CREATE: 'Thêm danh mục thiết bị', CATALOG_EDIT: 'Sửa danh mục thiết bị', CATALOG_DELETE: 'Xóa danh mục thiết bị', ADD_ROOM: 'Thêm thiết bị vào phòng', ROOM_QUANTITY: 'Thay đổi số lượng tại phòng',")
start=s.index('const filteredAssets = computed(() => {')
end=s.index('const { page: roomPage', start)
s=s[:start]+'''const filteredAssets = computed(() => roomInventory.value.filter(e => (!conditionFilter.value || e.condition === conditionFilter.value) && (!search.value || `${e.name} ${e.assetCode || ''} ${e.category}`.toLowerCase().includes(search.value.toLowerCase()))))
const { page, pageItems, totalItems } = usePagination(filteredAssets, [tab, roomId, search, conditionFilter])
const catalogRows = computed(() => catalogs.value.map(c => {
  const items = equipment.value.filter(e=>e.catalogId===c.id)
  const total = items.reduce((sum,e)=>sum+e.quantity,0)
  const allocated = items.filter(e=>e.roomId).reduce((sum,e)=>sum+e.quantity,0)
  return {...c,total,allocated,inStock:total-allocated,available:items.filter(e=>!e.roomId && e.condition==='TOT').reduce((sum,e)=>sum+e.quantity,0)}
}).filter(c=>(!catalogFilter.value || c.category===catalogFilter.value) && (!catalogEnabledFilter.value || String(c.enabled)===catalogEnabledFilter.value) && (!search.value || `${c.name} ${c.category}`.toLowerCase().includes(search.value.toLowerCase()))))
const {page:catalogPage,pageItems:catalogPageItems,totalItems:catalogTotal} = usePagination(catalogRows,[search,catalogFilter,catalogEnabledFilter])
const warehouseStock = computed(() => equipment.value.filter(e=>!e.roomId && (!stockCatalogId.value || e.catalogId===stockCatalogId.value) && (!conditionFilter.value || e.condition===conditionFilter.value)))
const {page:stockPage,pageItems:stockPageItems,totalItems:stockTotal} = usePagination(warehouseStock,[stockCatalogId,conditionFilter])
const selectedStock = computed(() => equipment.value.find(e=>String(e.id)===String(form.stockId)))
const availableStock = computed(() => equipment.value.filter(e=>!e.roomId && e.condition==='TOT' && catalogs.value.some(c=>c.id===e.catalogId && c.enabled)))
const selectedReceiptCatalog = computed(() => catalogs.value.find(c=>String(c.id)===String(form.catalogId)))
const warehouseSummary = computed(() => [
  {label:'Danh mục thiết bị',value:catalogs.value.length,color:'text-ink'},
  {label:'Tổng số lượng',value:equipment.value.reduce((sum,e)=>sum+e.quantity,0),color:'text-brand'},
  {label:'Đã cấp cho phòng',value:equipment.value.filter(e=>e.roomId).reduce((sum,e)=>sum+e.quantity,0),color:'text-emerald-600'},
  {label:'Còn trong kho',value:equipment.value.filter(e=>!e.roomId).reduce((sum,e)=>sum+e.quantity,0),color:'text-slate-600'},
  {label:'Kho cần xử lý',value:equipment.value.filter(e=>!e.roomId && e.condition!=='TOT').reduce((sum,e)=>sum+e.quantity,0),color:'text-amber-600'}
])
'''+s[end:]
s=s.replace('equipment.value = data.equipment; nodes.value = data.nodes','equipment.value = data.equipment; nodes.value = data.nodes; catalogs.value = data.catalogs || []')
s=s.replace("if (roomId.value && !(tab.value === 'allocation' && locationFilter.value === 'warehouse'))", "if (roomId.value && tab.value !== 'warehouse')")
s=s.replace("watch([tab, locationFilter],", "watch(tab,")
start=s.index('function openModal(action, asset = null)')
end=s.index("const modalError = ref('')",start)
s=s[:start]+'''function openModal(action, asset = null) {
  error.value = ''; success.value = ''; selectedAsset.value = asset
  Object.assign(form, {name:asset?.name || '',category:asset?.category || 'Khác',quantity:asset?.quantity || 1,trackingMode:asset?.trackingMode || 'BULK',assetCode:'',
    condition:Object.keys(conditions).find(c=>c!==asset?.condition) || 'HONG',note:'',actualCount:asset?.quantity || 0,
    targetRoomId:roomId.value,catalogId:action==='RECEIPT' ? String(asset?.id || '') : '',stockId:'',enabled:asset?.enabled ?? true})
  modal.value = action
}
'''+s[end:]
start=s.index("    if (modal.value === 'RECEIPT') {")
end=s.index("    } else if (modal.value === 'CONDITION')",start)
s=s[:start]+'''    if (modal.value === 'CATALOG_CREATE' || modal.value === 'CATALOG_EDIT') {
      path='/admin/assets/catalogs'+(modal.value==='CATALOG_EDIT'?`/${asset.id}`:''); method=modal.value==='CATALOG_EDIT'?'patch':'post'
      payload={name:form.name,category:form.category,trackingMode:form.trackingMode,enabled:form.enabled,version:asset?.version || 1}
    } else if (modal.value==='CATALOG_DELETE') {
      path=`/admin/assets/catalogs/${asset.id}?version=${asset.version}`; method='delete'
    } else if (modal.value==='ADD_ROOM') {
      if(!selectedStock.value) throw new Error('Chọn thiết bị trong kho.')
      path=`/admin/assets/rooms/${roomId.value}/equipment`
      payload={equipmentId:selectedStock.value.id,quantity:Number(form.quantity),version:selectedStock.value.version,note:form.note}
    } else if (modal.value==='ROOM_QUANTITY') {
      path=`/admin/assets/${asset.id}/room-quantity`
      payload={actualCount:Number(form.actualCount),version:asset.version,note:form.note}
    } else if (modal.value === 'RECEIPT') {
      const catalog=selectedReceiptCatalog.value
      if(!catalog) throw new Error('Chọn danh mục thiết bị.')
      path='/admin/assets/receipts'
      payload={catalogId:catalog.id,name:catalog.name,category:catalog.category,quantity:catalog.trackingMode==='INDIVIDUAL'?1:Number(form.quantity),trackingMode:catalog.trackingMode,assetCode:catalog.trackingMode==='INDIVIDUAL'?form.assetCode:null,note:form.note}
'''+s[end:]
# Header and common room layout.
s=s.replace("<button v-if=\"tab === 'allocation'\" @click=\"openModal('RECEIPT')\"", "<button v-if=\"tab === 'warehouse'\" @click=\"openModal('CATALOG_CREATE')\"")
s=s.replace('+ Nhập kho</button>','+ Thêm thiết bị</button>')
s=s.replace("<section v-if=\"tab!=='iot'\"", "<section v-if=\"tab==='assets'\"")
s=s.replace("{{ tab==='assets' ? 'Tổng quan tài sản' : 'Tổng quan phân bổ thiết bị' }}",'Tổng quan tài sản')
s=s.replace("<span v-if=\"tab==='allocation'\">. Kho khả dụng tính trên toàn bộ kho.</span>",'')
s=s.replace('<aside class="overflow-hidden', '<aside v-if="tab!==\'warehouse\'" class="overflow-hidden')
s=s.replace('<section class="min-w-0 space-y-5">','<section class="min-w-0 space-y-5" :class="tab===\'warehouse\' ? \'xl:col-span-2\' : \'\'">')
s=s.replace('<div class="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm">\n              <h2', '<div v-if="tab!==\'warehouse\'" class="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm">\n              <h2',1)
s=s.replace('<template v-else>\n              <div class="rounded-2xl', '<template v-else-if="tab===\'assets\'">\n              <div class="rounded-2xl',1)
s=s.replace('<h3 class="mb-4 text-sm font-semibold text-ink">Bộ lọc tài sản</h3>', '''<div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 class="text-sm font-semibold text-ink">Tài sản tại phòng</h3><button :disabled="!roomId || busy" @click="openModal('ADD_ROOM')" class="rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">+ Thêm thiết bị</button></div>''')
s='\n'.join(line for line in s.split('\n') if 'v-model="locationFilter"' not in line)
s=s.replace("{{ tab==='assets' ? 'Số lượng chỉ đọc. Báo hoặc chuyển tình trạng một phần tài sản không làm thay đổi tổng số lượng của phòng.' : 'Nhập kho, cấp phát, thu hồi và điều chuyển tài sản phòng. Bộ thiết bị mượn trong tủ được quản lý riêng.' }}", 'Tăng số lượng lấy thêm từ kho; giảm số lượng trả về kho. Đổi tình trạng không làm thay đổi tổng số lượng thiết bị.')
start=s.index('                      <button v-if="tab===\'assets\'"')
end=s.index('\n                    </div></td>',start)
s=s[:start]+'''                      <button @click="openModal('ROOM_QUANTITY',asset)" class="rounded-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-brand">Thay đổi số lượng</button>
                      <button @click="openModal('CONDITION',asset)" class="rounded-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-brand">Báo / đổi tình trạng</button>'''+s[end:]
s=s.replace('Nhập kho và phân bổ để bổ sung tài sản phòng.','Chọn Thêm thiết bị để lấy thiết bị từ kho vào phòng.')
# Modal body fully follows new workflows.
start=s.index('        <template v-if="modal===\'RECEIPT\'">')
end=s.index('        <p v-if="modalError"',start)
s=s[:start]+'''        <template v-if="modal==='CATALOG_CREATE' || modal==='CATALOG_EDIT'">
          <div><label for="catalog-name" class="modal-label">Tên thiết bị</label><input id="catalog-name" v-model="form.name" required maxlength="100" class="modal-field" /></div>
          <div><label for="catalog-category" class="modal-label">Phân loại</label><input id="catalog-category" v-model="form.category" required maxlength="50" class="modal-field" /></div>
          <div><label for="catalog-tracking" class="modal-label">Cách quản lý</label><select id="catalog-tracking" v-model="form.trackingMode" :disabled="modal==='CATALOG_EDIT'" class="modal-field"><option value="BULK">Theo số lượng</option><option value="INDIVIDUAL">Theo từng chiếc</option></select></div>
          <div><label for="catalog-enabled" class="modal-label">Trạng thái danh mục</label><select id="catalog-enabled" v-model="form.enabled" class="modal-field"><option :value="true">Đang sử dụng</option><option :value="false">Ngừng sử dụng</option></select></div>
        </template>
        <p v-if="modal==='CATALOG_DELETE'" class="text-sm text-slate-600">Xóa danh mục {{ selectedAsset?.name }}? Chỉ được xóa khi không còn thiết bị trong kho hoặc tại phòng. Danh mục còn thiết bị có thể chuyển sang Ngừng sử dụng.</p>
        <template v-if="modal==='RECEIPT'">
          <div><label for="receipt-catalog" class="modal-label">Danh mục thiết bị</label><select id="receipt-catalog" v-model="form.catalogId" required class="modal-field"><option value="" disabled>Chọn danh mục</option><option v-for="c in catalogs.filter(c=>c.enabled)" :key="c.id" :value="String(c.id)">{{ c.name }} · {{ c.category }}</option></select></div>
          <div v-if="selectedReceiptCatalog?.trackingMode==='INDIVIDUAL'"><label for="asset-code" class="modal-label">Mã thiết bị duy nhất</label><input id="asset-code" v-model="form.assetCode" required maxlength="80" class="modal-field" /><p class="mt-2 text-xs text-slate-500">Mỗi lần nhập một chiếc, số lượng bằng 1.</p></div>
        </template>
        <template v-if="modal==='ADD_ROOM'">
          <div><label for="room-stock" class="modal-label">Thiết bị khả dụng trong kho</label><select id="room-stock" v-model="form.stockId" required class="modal-field"><option value="" disabled>Chọn thiết bị</option><option v-for="e in availableStock" :key="e.id" :value="String(e.id)">{{ e.name }} · {{ e.assetCode || e.category }} · còn {{ e.quantity }}</option></select></div>
          <p v-if="!availableStock.length" class="text-sm text-amber-700">Kho chưa có thiết bị sử dụng tốt. Nhập thiết bị trong tab Kho thiết bị trước.</p>
          <p class="text-xs text-slate-500">Phòng nhận: {{ selectedRoom?.name }}</p>
        </template>
        <div v-if="['ADD_ROOM','CONDITION'].includes(modal) || (modal==='RECEIPT' && selectedReceiptCatalog?.trackingMode!=='INDIVIDUAL')"><label for="asset-quantity" class="modal-label">{{ modal==='CONDITION' ? 'Số lượng chuyển tình trạng' : 'Số lượng' }}</label><input id="asset-quantity" v-model.number="form.quantity" type="number" min="1" :max="modal==='ADD_ROOM' ? selectedStock?.quantity || 1 : modal==='CONDITION' ? selectedAsset?.quantity || 1 : 10000" required step="1" class="modal-field" /></div>
        <div v-if="modal==='COUNT' || modal==='ROOM_QUANTITY'"><label for="asset-actual" class="modal-label">Số lượng mới</label><input id="asset-actual" v-model.number="form.actualCount" type="number" min="0" :max="selectedAsset?.trackingMode==='INDIVIDUAL'?1:10000" required step="1" class="modal-field" /><p v-if="modal==='ROOM_QUANTITY'" class="mt-2 text-xs text-slate-500">Tăng lấy thêm từ kho; giảm trả về kho, giữ nguyên tình trạng. Thiết bị riêng lẻ nhập 0 để trả về kho.</p></div>
        <div v-if="modal==='CONDITION'"><label for="asset-condition" class="modal-label">Tình trạng mới</label><select id="asset-condition" v-model="form.condition" required class="modal-field"><option v-for="(name,key) in conditions" :key="key" :value="key" :disabled="key===selectedAsset?.condition">{{ name }}</option></select></div>
        <div v-if="!modal.startsWith('CATALOG_')"><label for="asset-note" class="modal-label">{{ modal==='RECEIPT' ? 'Ghi chú' : 'Lý do / ghi chú (bắt buộc)' }}</label><textarea id="asset-note" v-model="form.note" :required="modal!=='RECEIPT'" maxlength="255" class="modal-field" /></div>
'''+s[end:]
# Insert warehouse content before assets branch.
anchor='            <template v-else-if="tab===\'assets\'">'
warehouse=Path('.codex-temp/assets/warehouse-template.txt').read_text(encoding='utf-8')
s=s.replace(anchor,warehouse+'\n'+anchor)
p.write_text(s,encoding='utf-8')
