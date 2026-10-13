from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8')
start=s.index('              <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">')
end=s.index('\n              <div class="flex flex-wrap gap-x-5', start)
summary=s[start:end]
s=s[:start]+s[end:]
anchor='        <div class="grid items-start gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">'
summary='        <section v-if="tab === \'iot\'" class="mb-5 space-y-3" aria-label="Thống kê node tổng quát">\n          <h2 class="text-sm font-semibold text-ink">Tổng quan node IoT</h2>\n'+summary+'\n        </section>\n'
s=s.replace(anchor,summary+anchor)
start=s.index('                <div class="mt-3 rounded-xl border border-blue-100 bg-blue-50/40 p-3 text-sm">')
end=s.index('\n                <div class="mt-4 grid grid-cols-2',start)
result=s[start:end]
result=result.replace('                <div class="mt-3 rounded-xl border border-blue-100 bg-blue-50/40 p-3 text-sm">','                <section class="mt-4 rounded-xl border border-blue-100 bg-blue-50/40 p-4 text-sm" aria-label="Kết quả phân tích AI">\n                  <div class="mb-3 flex flex-wrap items-center justify-between gap-2"><h4 class="font-semibold text-ink">Kết quả phân tích AI</h4><span class="rounded-lg bg-white px-2 py-1 text-xs text-slate-500">Nhận định theo quy tắc</span></div>')
result=result.rsplit('</div>',1)[0]+'</section>'
s=s[:start]+s[end:]
anchor='              </div>\n              <div v-if="selectedNodes.length"'
assert anchor in s
s=s.replace(anchor,result+'\n'+anchor,1)
p.write_text(s,encoding='utf-8')
