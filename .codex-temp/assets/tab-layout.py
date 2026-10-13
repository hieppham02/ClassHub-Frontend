from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8')
anchor='        <div class="grid items-start gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">'
summary='''        <section v-if="tab!=='iot'" class="mb-5 space-y-3" aria-label="Thống kê tài sản tổng quát">
          <h2 class="text-sm font-semibold text-ink">{{ tab==='assets' ? 'Tổng quan tài sản' : 'Tổng quan phân bổ thiết bị' }}</h2>
          <div class="grid grid-cols-2 gap-3 lg:grid-cols-5"><div v-for="item in assetOverview" :key="item.label" class="rounded-xl border border-blue-100 bg-white p-4"><p class="text-xs text-slate-500">{{ item.label }}</p><b class="mt-2 block text-2xl" :class="item.color">{{ item.value }}</b></div></div>
          <p class="text-xs text-slate-500">Tài sản tại phòng · {{ nodeStatisticsScope }}<span v-if="tab==='allocation'">. Kho khả dụng tính trên toàn bộ kho.</span></p>
        </section>
'''
s=s.replace(anchor,summary+anchor)
anchor='            </div>\n            <div class="max-h-80 overflow-y-auto'
filter='''              <div v-if="tab==='iot'"><label for="node-filter" class="mb-1 block text-xs text-slate-500">Tình trạng node</label><select id="node-filter" v-model="nodeFilter" class="h-11 w-full rounded-xl border border-blue-100 bg-white px-3 text-sm"><option value="">Tất cả tình trạng</option><option value="ACTIVE">Đang hoạt động</option><option value="ONLINE">Trực tuyến</option><option value="OFFLINE">Ngoại tuyến</option><option value="DISABLED">Đang bảo trì</option></select></div>
'''
assert anchor in s
s=s.replace(anchor,filter+anchor)
s=s.replace('class="h-10 w-full rounded-xl border border-blue-100 bg-white px-3 text-xs text-ink outline-none', 'class="h-10 w-full rounded-xl border border-blue-100 bg-white px-3 text-[11px] text-ink outline-none')
s=s.replace('v-for="node in selectedNodes"','v-for="node in visibleNodes"').replace('v-if="selectedNodes.length"','v-if="visibleNodes.length"').replace('v-for="n in selectedNodes"','v-for="n in visibleNodes"')
anchor='              <div v-if="!selectedNodes.length"'
index=s.index(anchor)
s=s[:index]+'''              <div v-if="selectedNodes.length && !visibleNodes.length" class="rounded-2xl border border-blue-100 bg-white p-6 text-sm text-slate-500">Không có node phù hợp với bộ lọc.</div>
'''+s[index:]
s=s.replace('              <div class="flex flex-wrap gap-3">\n                <input v-model="search"', '              <div class="rounded-2xl border border-blue-100 bg-white p-5 shadow-sm">\n              <h3 class="mb-4 text-sm font-semibold text-ink">Bộ lọc tài sản</h3>\n              <div class="flex flex-wrap gap-3">\n                <input v-model="search"')
anchor='              <div class="overflow-hidden rounded-2xl border border-blue-100 bg-white shadow-sm">\n                <div class="overflow-x-auto"><table'
s=s.replace(anchor, '              </div>\n'+anchor,1)
s=s.replace('<p class="text-xs leading-relaxed text-slate-500">{{ tab', '<p class="mt-3 text-xs leading-relaxed text-slate-500">{{ tab')
p.write_text(s,encoding='utf-8')
