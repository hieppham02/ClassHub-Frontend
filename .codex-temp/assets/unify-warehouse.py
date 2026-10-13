from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8').replace("const stockCatalogId = ref(null)", "const stockCatalogId = ref(null)\nconst stockConditionFilter = ref('')\nfunction showWarehouseDetails(id) { stockCatalogId.value=id; stockConditionFilter.value='' }")
s=s.replace("(!conditionFilter.value || e.condition===conditionFilter.value)))", "(!stockConditionFilter.value || e.condition===stockConditionFilter.value)))")
s=s.replace('usePagination(warehouseStock,[stockCatalogId,conditionFilter])','usePagination(warehouseStock,[stockCatalogId,stockConditionFilter])')
s=s.replace('@click="stockCatalogId=c.id"', '@click="showWarehouseDetails(c.id)"').replace('>Tình trạng</button>', '>Quản lý tồn kho</button>')
s=s.replace('<td class="px-5 py-4">{{ c.inStock }}</td>', '''<td class="px-5 py-4">{{ c.inStock }}<div class="mt-1 flex flex-wrap gap-1"><span v-for="(label,key) in conditions" :key="key" v-show="equipment.some(e=>e.catalogId===c.id && !e.roomId && e.condition===key)" class="rounded bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-500">{{ label }}: {{ equipment.filter(e=>e.catalogId===c.id && !e.roomId && e.condition===key).reduce((sum,e)=>sum+e.quantity,0) }}</span></div></td>''')
lines=s.splitlines()
index=next(i for i,line in enumerate(lines) if '<h3 class="text-sm font-semibold text-ink">Số lượng và tình trạng trong kho</h3>' in line)
details=lines.pop(index).strip()
start=details.index('<div class="overflow-x-auto">')
details=details[start:]
details=details.removesuffix('</div>')
details=details.replace('<select v-model="conditionFilter"','<select v-model="stockConditionFilter"')
s='\n'.join(lines)+'\n'
modal='''    <AppModal v-if="stockCatalogId" :title="`Tồn kho · ${catalogs.find(c=>c.id===stockCatalogId)?.name || ''}`" size="lg" :busy="busy" @close="stockCatalogId=null">
      <div class="mb-4"><label for="stock-condition" class="modal-label">Tình trạng</label><select id="stock-condition" v-model="stockConditionFilter" class="modal-field"><option value="">Tất cả tình trạng</option><option v-for="(name,key) in conditions" :key="key" :value="key">{{ name }}</option></select></div>
'''+details+'''
      <template #footer><button @click="stockCatalogId=null" :disabled="busy" class="modal-cancel">Đóng</button></template>
    </AppModal>
'''
anchor='    <AppModal v-if="modal" :title="actions[modal]"'
assert anchor in s
s=s.replace(anchor,modal+anchor).replace(':title="actions[modal]" size="md"', ':title="actions[modal]" :layer="stockCatalogId ? \'nested\' : \'normal\'" size="md"')
s=s.replace('if (!busy.value && !modal.value)', 'if (!busy.value && !modal.value && !stockCatalogId.value)')
p.write_text(s,encoding='utf-8')
