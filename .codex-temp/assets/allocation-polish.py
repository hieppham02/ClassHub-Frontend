from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8').replace('<TablePagination ', '<TablePagination hide-summary ')
anchor='              <h3 class="mb-4 text-sm font-semibold text-ink">Bộ lọc tài sản</h3>'
s=s.replace(anchor,'''              <div class="mb-4 flex flex-wrap items-center justify-between gap-3"><h3 class="text-sm font-semibold text-ink">{{ tab==='allocation' ? 'Phân bổ thiết bị' : 'Bộ lọc tài sản' }}</h3><button v-if="tab==='allocation'" @click="openModal('RECEIPT')" class="rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-white">+ Nhập thiết bị vào kho</button></div>
              <p v-if="tab==='allocation'" class="mb-4 text-xs text-slate-500">Nhập kho → chọn thiết bị và số lượng → phân bổ vào phòng nhận. Chọn “Tại phòng đang chọn” để thu hồi hoặc điều chuyển.</p>''')
p.write_text(s,encoding='utf-8')
