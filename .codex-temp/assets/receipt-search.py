from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8').replace('v-for="c in catalogs.filter(c=>c.enabled)"','v-for="c in receiptCatalogs"')
p.write_text(s,encoding='utf-8')
