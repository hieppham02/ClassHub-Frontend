from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8').replace('<TablePagination hide-summary ', '<TablePagination ')
start=s.index('              <div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3')
end=s.index('              <div class="flex flex-wrap gap-3">',start)
s=s[:start]+'              <h3 class="mb-4 text-sm font-semibold text-ink">Bộ lọc tài sản</h3>\n'+s[end:]
p.write_text(s,encoding='utf-8')
