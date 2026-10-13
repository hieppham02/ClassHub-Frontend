from pathlib import Path

p = Path('src/views/client/HomeView.vue')
s = p.read_text(encoding='utf-8')
s = s.replace("const damageLocation = ref(null)", "const damageLocation = ref(null)\nconst showDamageReport = ref(false)\nconst damageLocationId = ref('')")
s = s.replace("  damageLocation.value = location\n", "  showDamageReport.value = true\n  damageLocation.value = location\n  damageLocationId.value = location?.id || ''\n")
s = s.replace("    await api.post('/damage-reports', { roomId: damageLocation.value.id,", "    await api.post('/damage-reports', { roomId: damageLocationId.value,")
s = s.replace("    damageLocation.value = null\n    showSuccessToast", "    showDamageReport.value = false\n    damageLocation.value = null\n    showSuccessToast")
s = s.replace("'bg-red-400 border-red-600 opacity-80': getCabinetStatus(cab) === 'MAINTENANCE',\n                    'corridor-cabinet': cab.locationType === 'CORRIDOR'", "'bg-red-400 border-red-600 opacity-80': getCabinetStatus(cab) === 'MAINTENANCE'")
s = s.replace('<span v-if="cab.locationType === \'CORRIDOR\'" class="text-[10px] font-bold text-slate-800">Hành lang · Đồ dùng chung</span>', '<span v-if="cab.locationType === \'CORRIDOR\'" class="text-[10px] font-bold text-slate-800">Hành lang</span>')
s = s.replace('                  <button type="button" @click.stop="openDamageReport(cab)" class="rounded-md bg-white/85 px-2 py-1 text-[10px] font-semibold text-red-700 hover:bg-white" :aria-label="`Báo hỏng hóc tại ${cab.name}`">Báo hỏng hóc</button>\n', '')
s = s.replace('''            <span>Bảo trì / Mất kết nối</span>
          </div>
        </div>''', '''            <span>Bảo trì / Mất kết nối</span>
          </div>
          <button type="button" @click="openDamageReport(null)" class="ml-auto inline-flex h-9 items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 text-xs font-semibold text-red-700 transition hover:bg-red-100">Báo hỏng hóc</button>
        </div>''')
s = s.replace('<AppModal v-if="damageLocation" title="Báo cáo hỏng hóc" layer="nested" :busy="sendingDamage" @close="damageLocation = null">', '<AppModal v-if="showDamageReport" title="Báo cáo hỏng hóc" layer="nested" :busy="sendingDamage" @close="showDamageReport = false">')
s = s.replace('<p class="text-sm text-slate-500">{{ damageLocation.name }} · {{ damageLocation.floor }} · {{ damageLocation.building }}</p>', '''<label class="block text-sm font-semibold">Phòng / tủ cần báo hỏng
          <select v-model="damageLocationId" required class="modal-field mt-2 w-full">
            <option disabled value="">Chọn phòng hoặc tủ hành lang</option>
            <option v-for="location in rooms" :key="location.id" :value="location.id">{{ location.name }} · {{ location.floor }} · {{ location.building }}</option>
          </select>
        </label>''')
s = s.replace('@click="damageLocation = null">Hủy', '@click="showDamageReport = false">Hủy')
s = s.replace('<template #footer><button type="button" class="modal-cancel text-red-600" @click="openDamageReport(selectedCabinet)">Báo hỏng hóc</button><button', '<template #footer><button')
s = s.replace('.corridor-cabinet { grid-column: span 2; height: 180px; }\n', '')
s = s.replace('gap: 8px; width: 88%; height: 95px;', 'gap: 4px; width: 88%; height: 38px;')
s = s.replace('right: 8px; top: 40%; height: 25px; width: 4px;', 'right: 5px; top: 30%; height: 14px; width: 3px;')
p.write_text(s, encoding='utf-8')

p = Path('docs/database/corridor-cabinets.sql')
s = p.read_text(encoding='utf-8').replace("CONCAT('Tủ tự do ',p.position,' · Tầng ',f.floor)", "CONCAT('Tủ tự do · Tầng ',f.floor)").replace('(SELECT 1 AS position UNION ALL SELECT 2)', '(SELECT 1 AS position)')
p.write_text(s, encoding='utf-8')

p = Path('.codex-temp/corridor/migrate.py')
s = p.read_text(encoding='utf-8').replace('SUM(COALESCE(floor_count,1))*2', 'SUM(COALESCE(floor_count,1))').replace('two per floor', 'one per floor')
p.write_text(s, encoding='utf-8')
