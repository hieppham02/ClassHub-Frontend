from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8')
s=s.replace("const editingNode = ref(null)\nconst nodeMode = ref('ACTIVE')\nconst nodeError = ref('')\n", '')
start=s.index('function editNode(node)')
end=s.index('\nlet powerRequestId',start)
s=s[:start]+'''async function saveNode(node, event) {
  const previous = node.status === 'DISABLED' ? 'DISABLED' : 'ACTIVE'
  const status = event.target.value
  if (busy.value || status === previous) return
  busy.value = true; error.value = ''
  try {
    await api.patch(`/admin/assets/nodes/${node.id}/status`, { status })
    await refresh(true)
  } catch(err) { event.target.value = previous; error.value = err.message }
  finally { busy.value = false }
}
'''+s[end:]
s=s.replace(' && !editingNode.value','')
s=s.replace('grid grid-cols-2 gap-3 lg:grid-cols-4', 'grid grid-cols-2 gap-3 lg:grid-cols-5')
s=s.replace("[{label:'Đang hoạt động',value:nodeTotals.active", "[{label:'Tổng số node',value:statisticsNodes.length,color:'text-ink'},{label:'Đang hoạt động',value:nodeTotals.active")
start=s.index('                <div class="flex flex-wrap items-center justify-between gap-3"><div><h3')
end=s.index('\n                <div class="mt-4 grid',start)
s=s[:start]+'''                <div class="flex flex-wrap items-start justify-between gap-4">
                  <div><h3 class="font-semibold text-ink">{{ nodeDisplayName(node) }}</h3><p class="mt-1 text-xs text-slate-500">{{ nodeDisplayCode(node) }}</p><p class="mt-3 text-xs text-slate-500">Lần nhận gần nhất: {{ dateTime(node.lastSeenAt) }}</p></div>
                  <div class="flex w-40 flex-col items-end gap-3">
                    <span :class="node.status==='DISABLED' ? 'bg-amber-50 text-amber-700' : node.status==='ONLINE' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'" class="rounded-lg px-3 py-1 text-xs font-bold">{{ node.status==='DISABLED' ? 'Bảo trì' : node.status==='ONLINE' ? 'Trực tuyến' : 'Ngoại tuyến' }}</span>
                    <div class="w-full"><label :for="`node-status-${node.id}`" class="mb-1 block text-xs text-slate-500">Trạng thái</label><select :id="`node-status-${node.id}`" :value="node.status==='DISABLED' ? 'DISABLED' : 'ACTIVE'" :disabled="busy" @change="saveNode(node,$event)" class="h-10 w-full rounded-xl border border-blue-100 bg-white px-3 text-xs text-ink outline-none focus:ring-2 focus:ring-brand disabled:opacity-50"><option value="ACTIVE">Đang hoạt động</option><option value="DISABLED">Đang bảo trì</option></select></div>
                  </div>
                </div>'''+s[end:]
start=s.index('    <AppModal v-if="editingNode"')
end=s.index('    <AppModal v-if="modal"',start)
s=s[:start]+s[end:]
p.write_text(s,encoding='utf-8')
