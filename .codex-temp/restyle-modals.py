from pathlib import Path
import re

ROOT = Path('src/views')
IMPORT = "import AppModal from '@/components/shared/AppModal.vue'\n"

def read(name):
    path = ROOT / name
    text = path.read_text(encoding='utf-8')
    assert IMPORT not in text
    return path, text.replace('<script setup>\n', '<script setup>\n' + IMPORT, 1)

def fields(block):
    block = re.sub(r'(<(?:input|select|textarea)\b[^>]*?\s)class="[^"]*"', r'\1class="modal-field"', block)
    block = re.sub(r'(<label\b[^>]*?\s)class="[^"]*"', r'\1class="modal-label"', block)
    # Allow narrow mobile screens to use a single column without squeezing fields.
    return block.replace('grid grid-cols-2 gap-3', 'grid grid-cols-1 gap-4 sm:grid-cols-2')

for name, title, size, forms in [
    ('admin/AccountsView.vue', "isEditing ? 'Chỉnh sửa tài khoản' : 'Thêm mới tài khoản'", 'lg', ['saveAccount']),
    ('admin/BuildingsView.vue', "(isEditing ? 'Chỉnh sửa' : 'Thêm mới') + ' ' + (activeTab === 'buildings' ? 'Tòa nhà' : 'Phòng học')", 'md', ['saveBuilding', 'saveRoom']),
]:
    path, text = read(name)
    start = text.index('<div v-if="showModal"')
    end = text.index('\n    </div>\n  </AdminLayout>', start)
    old = text[start:end]
    bodies = []
    for i, handler in enumerate(forms):
        form = re.search(r'<form\b[^>]*@submit.prevent="' + handler + r'">([\s\S]*?)</form>', old)
        assert form
        body = form.group(1)
        body = body[:body.index('<div class="mt-6 flex justify-end')].rstrip()
        condition = '' if len(forms) == 1 else (' v-if="activeTab === \'buildings\'"' if i == 0 else ' v-else')
        bodies.append(f'<form{condition} id="modal-editor" class="space-y-4" @submit.prevent="{handler}">\n{fields(body)}\n          </form>')
    confirm = "{{ isEditing ? 'Lưu thay đổi' : 'Tạo tài khoản' }}" if len(forms) == 1 else 'Lưu'
    replacement = f'''<AppModal v-if="showModal" :title="{title}" size="{size}" @close="closeModal">
          {chr(10).join(bodies)}
          <template #footer>
            <button type="button" @click="closeModal" class="modal-cancel">Hủy</button>
            <button type="submit" form="modal-editor" class="modal-primary">{confirm}</button>
          </template>
        </AppModal>
'''
    path.write_text(text[:start] + replacement + text[end:], encoding='utf-8')

path, text = read('admin/StatisticsView.vue')
start = text.index('<div v-if="showFilterModal"')
end = text.index('\n      <!-- Header -->', start)
old = text[start:end]
body_start = old.index('<div class="p-5 sm:p-6 flex flex-col gap-5">')
body_end = old.index('<div class="bg-slate-50 p-4 border-t', body_start)
body = old[body_start:body_end].rstrip()
body = body.replace('<div class="p-5 sm:p-6 flex flex-col gap-5">', '<div class="flex flex-col gap-5">')
# Existing labels include their controls; preserve the grid structure.
body = fields(body).replace('class="modal-label">Gom nhóm theo', 'class="grid gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Gom nhóm theo').replace('class="modal-label">Từ ngày', 'class="grid gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Từ ngày').replace('class="modal-label">Đến ngày', 'class="grid gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">Đến ngày')
replacement = f'''<AppModal v-if="showFilterModal" title="Bộ lọc thống kê" @close="showFilterModal = false">
          {body}
          <template #footer>
            <button type="button" @click="showFilterModal = false" class="modal-cancel">Hủy</button>
            <button type="button" @click="applyFilter" :disabled="tempFilters.dateFrom && tempFilters.dateTo && tempFilters.dateFrom > tempFilters.dateTo" class="modal-primary">Áp dụng</button>
          </template>
        </AppModal>
'''
path.write_text(text[:start] + replacement + text[end:], encoding='utf-8')

path, text = read('admin/CabinetsView.vue')
start = text.index('<div v-if="confirmModal.show"')
end = text.index('    <!-- Toast Notification', start)
old = text[start:end]
button_start = old.index('<button @click="executeModalAction"')
button_end = old.index('</button>', button_start) + len('</button>')
button = old[button_start:button_end]
button = re.sub(r':class="\{[\s\S]*?\}"', ':class="{ \'modal-warning\': confirmModal.confirmVariant === \'warning\', \'modal-danger\': confirmModal.confirmVariant === \'danger\' }"', button, count=1)
button = re.sub(r'\n\s*class="[^"]*"', '\n            class="modal-primary"', button, count=1)
replacement = f'''<AppModal v-if="confirmModal.show" :title="confirmModal.title" size="md" :busy="confirmModal.isProcessing" @close="closeConfirmModal">
      <p class="text-sm leading-relaxed text-slate-500">{{{{ confirmModal.message }}}}</p>
      <div class="mt-4 flex items-center justify-between gap-3 rounded-xl border border-blue-100 bg-blue-50/40 p-3 text-sm">
        <span class="text-slate-500">Tủ tác động</span><span class="font-semibold text-ink">{{{{ confirmModal.cabName }}}}</span>
      </div>
      <template #footer>
        <button type="button" @click="closeConfirmModal" :disabled="confirmModal.isProcessing" class="modal-cancel">Hủy</button>
        {button}
      </template>
    </AppModal>

'''
path.write_text(text[:start] + replacement + text[end:], encoding='utf-8')

path, text = read('client/InfoView.vue')
start = text.index('<div v-if="showLogoutModal"')
end = text.index('    <BottomNav', start)
replacement = '''<AppModal v-if="showLogoutModal" title="Xác nhận đăng xuất" @close="cancelLogout">
      <p class="text-sm leading-relaxed text-slate-500">Bạn sẽ cần đăng nhập lại với mã tài khoản và mật khẩu để tiếp tục sử dụng hệ thống.</p>
      <template #footer>
        <button type="button" @click="cancelLogout" class="modal-cancel">Hủy</button>
        <button type="button" @click="logout" class="modal-primary">Đăng xuất</button>
      </template>
    </AppModal>

'''
path.write_text(text[:start] + replacement + text[end:], encoding='utf-8')

path, text = read('client/HomeView.vue')
start = text.index('<div v-if="showMissingSlotModal"')
end = text.index('  <main ', start)
replacement = '''<AppModal v-if="showMissingSlotModal" title="Chọn ca học" @close="showMissingSlotModal = false">
    <p class="text-sm leading-relaxed text-slate-500">Vui lòng chọn ca học trước khi đăng ký mượn thiết bị.</p>
    <template #footer><button type="button" @click="showMissingSlotModal = false" class="modal-primary">Đã hiểu</button></template>
  </AppModal>

  <AppModal v-if="confirmReturnId" title="Gửi yêu cầu trả thiết bị" :busy="returning" @close="confirmReturnId = null">
    <div class="space-y-4">
      <p class="text-sm leading-relaxed text-slate-500">Hãy đảm bảo bạn đã cất đầy đủ chìa khóa, micro và đóng chặt cửa tủ.</p>
      <label class="modal-label" for="return-condition">Tình trạng trả</label>
      <select id="return-condition" v-model="returnCondition" class="modal-field">
        <option value="BINH_THUONG">Bình thường</option><option value="HONG_HOC">Có hỏng hóc</option><option value="MAT_DO">Thiếu thiết bị</option>
      </select>
      <label class="modal-label" for="return-note">Ghi chú</label>
      <textarea id="return-note" v-model="returnNote" maxlength="2000" placeholder="Mô tả thiết bị hỏng/thiếu" class="modal-field" />
    </div>
    <template #footer>
      <button type="button" :disabled="returning" @click="confirmReturnId = null" class="modal-cancel">Hủy</button>
      <button type="button" :disabled="returning" @click="returnRoom" class="modal-primary">Xác nhận trả</button>
    </template>
  </AppModal>

  <AppModal v-if="previewEquipment" :title="previewEquipment.name" size="md" layer="nested" @close="previewEquipment = null">
    <div class="flex min-h-[200px] items-center justify-center overflow-hidden rounded-xl border border-blue-100 bg-blue-50/30">
      <img v-if="previewEquipment.image" :src="previewEquipment.image" :alt="previewEquipment.name" class="max-h-[300px] max-w-full object-contain" />
      <p v-else class="px-4 py-10 text-center text-sm text-slate-500">Chưa có hình ảnh thực tế cho thiết bị này.</p>
    </div>
    <template #footer><button type="button" @click="previewEquipment = null" class="modal-cancel">Đóng</button></template>
  </AppModal>

'''
text = text[:start] + replacement + text[end:]
start = text.index('<div v-if="selectedCabinet"')
body_start = text.index('<div class="p-5 sm:p-6 overflow-y-auto flex-1">', start)
body_end = text.index('\n        </div>\n      </div>\n    </div>', body_start)
body = text[body_start + len('<div class="p-5 sm:p-6 overflow-y-auto flex-1">'):body_end]
body = fields(body)
body = body.replace('class="h-12 flex-1 sm:flex-none shrink-0 rounded-xl bg-slate-900 px-6 font-bold text-white transition hover:bg-slate-800"', 'class="modal-primary"')
body = body.replace('class="h-12 w-full rounded-xl border-2 border-blue-600 font-bold text-blue-600 hover:bg-blue-600 hover:text-white transition"', 'class="modal-cancel w-full"')
body = body.replace('class="h-12 w-full rounded-xl bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700 shadow-md"', 'class="modal-primary w-full"')
end = body_end + len('\n        </div>\n      </div>\n    </div>')
replacement = f'''<AppModal v-if="selectedCabinet" :title="'Tủ thiết bị ' + selectedCabinet.name" size="lg" layer="cabinet" @close="selectedCabinet = null; otpValue = ''">
      <template #subtitle>
        <span v-if="activeBooking && (activeBooking.room === selectedCabinet.id || activeBooking.roomId === selectedCabinet.id) && activeBooking.isCabinetOpen" class="mt-2 inline-flex rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-800">Tủ đang mở</span>
      </template>
      {body}
      <template #footer><button type="button" @click="selectedCabinet = null; otpValue = ''" class="modal-cancel">Đóng</button></template>
    </AppModal>'''
text = text[:start] + replacement + text[end:]
path.write_text(text, encoding='utf-8')
print('Updated all nine modal variants across six views; retained form submissions, bindings and action handlers.')
