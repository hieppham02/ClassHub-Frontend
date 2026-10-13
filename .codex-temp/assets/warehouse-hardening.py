from pathlib import Path
p=Path('.codex-temp/assets/backend/Controllers/AssetsController.cs')
s=p.read_text(encoding='utf-8')
s=s.replace('if(item.ma_phong!=null || item.TrackingMode!="BULK")', 'if(item.ma_phong!=null || (item.TrackingMode=="INDIVIDUAL" && request.ActualCount!=0))')
anchor='        var target=request.Action=="RETURN"?null:request.TargetRoomId?.Trim();'
s=s.replace(anchor,'''        if(request.Action!="RETURN" && !await context.EquipmentCatalogs.AnyAsync(c=>c.Id==item.CatalogId && c.Enabled)) return Conflict(new {message="Danh mục đã ngừng sử dụng."});
'''+anchor)
p.write_text(s,encoding='utf-8')
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8')
s=s.replace("  modal.value = action\n}","  if(action==='COUNT' && asset?.trackingMode==='INDIVIDUAL') form.actualCount=0\n  modal.value = action\n}")
s=s.replace('<button v-if="e.trackingMode===\'BULK\'" @click="openModal(\'COUNT\',e)" class="text-xs font-semibold text-brand">Thay đổi số lượng</button>', '<button @click="openModal(\'COUNT\',e)" class="text-xs font-semibold text-brand">{{ e.trackingMode===\'BULK\' ? \'Thay đổi số lượng\' : \'Xóa khỏi kho\' }}</button>')
s=s.replace(':max="selectedAsset?.trackingMode===\'INDIVIDUAL\'?1:10000"', ':max="selectedAsset?.trackingMode===\'INDIVIDUAL\'?(modal===\'COUNT\'?0:1):10000"')
p.write_text(s,encoding='utf-8')
