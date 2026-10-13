from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8')
blue='rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-600 hover:bg-blue-600 hover:text-white active:scale-95 transition border border-blue-200'
red='rounded-lg bg-red-50 px-2.5 py-1 text-xs font-bold text-red-600 hover:bg-red-600 hover:text-white active:scale-95 transition border border-red-200'
for handler in ["showWarehouseDetails(c.id)","openModal('RECEIPT',c)","openModal('CATALOG_EDIT',c)","openModal('CONDITION',e)"]:
    old='@click="'+handler+'" class="text-xs font-semibold text-brand"'
    assert old in s
    s=s.replace(old,'@click="'+handler+'" class="'+blue+'"')
s=s.replace('@click="openModal(\'CATALOG_DELETE\',c)" class="text-xs font-semibold text-red-600"', '@click="openModal(\'CATALOG_DELETE\',c)" class="'+red+'"')
s=s.replace('class="rounded-lg bg-blue-50 px-3 py-2 text-xs font-semibold text-brand"', 'class="'+blue+'"')
s=s.replace('@click="openModal(\'COUNT\',e)" class="text-xs font-semibold text-brand"', '@click="openModal(\'COUNT\',e)" :class="e.trackingMode===\'BULK\' ? \''+blue+'\' : \''+red+'\'"')
p.write_text(s,encoding='utf-8')
