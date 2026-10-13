from pathlib import Path
import json, re, shutil, hashlib
root=Path(__file__).resolve().parent
source=root.parents[1].parent/'Backend/ClassHub-API/ClassHub-API'
schema=json.loads((root/'schema-before.json').read_text(encoding='utf-8'))
tables={'cau_hinh_ca_hoc':'class_slot','nhat_ky_he_thong':'audit_log','phieu_muon':'borrowing_session','phong_hoc':'room','tai_khoan':'account','thiet_bi':'equipment','thiet_bi_iot':'cabinet','toa_nha':'building','iot_node':'iot_node','iot_sensor':'iot_sensor'}
columns={
'cau_hinh_ca_hoc':{'ca_id':'id','ten_ca':'name','gio_bat_dau':'start_time','gio_ket_thuc':'end_time','ghi_chu':'note'},
'nhat_ky_he_thong':{'ma_sv':'account_id','hanh_dong':'action','chi_tiet':'details','thoi_gian':'created_at'},
'phieu_muon':{'ma_sv':'borrower_id','ma_phong':'room_id','ngay_muon':'borrowing_date','ca_muon':'slot_id','trang_thai':'status','thoi_gian_tao':'created_at','thoi_gian_nhan':'received_at','thoi_gian_tra':'returned_at','ma_sv_tra':'returner_id','ma_sv_uy_quyen':'delegate_id','tinh_trang_tra':'return_condition','ghi_chu_tra':'return_note','ly_do_huy':'cancellation_reason'},
'phong_hoc':{'ma_phong':'id','ten_phong':'name','tang':'floor','suc_chua':'capacity','trang_thai':'status','ma_toa_nha':'building_id'},
'tai_khoan':{'ma_sv':'id','ho_ten':'full_name','mat_khau':'password_hash','sdt':'phone','vai_tro':'role','ten_lop':'class_or_department','trang_thai':'is_active','ngay_tao':'created_at'},
'thiet_bi':{'ten_thiet_bi':'name','so_luong':'quantity','tinh_trang':'condition','ghi_chu':'note','ma_phong':'room_id'},
'thiet_bi_iot':{'ma_phong':'room_id','ten_tu':'name','trang_thai_mang':'is_online','trang_thai_khoa':'lock_state','lan_cuoi_online':'last_seen_at'},
'toa_nha':{'ma_toa_nha':'id','ten_toa_nha':'name','so_tang':'floor_count','mo_ta':'description'},
'iot_node':{'ma_node':'node_code','ma_phong':'room_id','ten_node':'name','nguon_du_lieu':'data_source','trang_thai':'status','lan_cuoi_nhan':'last_seen_at','chu_ky_gui_giay':'publish_interval_seconds'},
'iot_sensor':{'thoi_gian_do':'measured_at','thoi_gian_nhan':'received_at','dong_ho_da_dong_bo':'clock_synced','nguon_du_lieu':'data_source'}}
assert set(tables)==set(schema), 'Unknown tables; review before migration'
def constraints(table):
    return [line.strip().rstrip(',') for line in schema[table]['ddl'].splitlines() if line.strip().startswith('CONSTRAINT ')]
def translate_constraint(text,table):
    before,sep,after=text.partition(' REFERENCES ')
    before=re.sub(r'`([^`]+)`', lambda m:'`'+columns[table].get(m[1],m[1])+'`',before)
    if sep:
        ref=re.match(r'`([^`]+)`',after)[1]
        after=re.sub(r'`([^`]+)`',lambda m:'`'+(tables[ref] if m[1]==ref else columns[ref].get(m[1],m[1]))+'`',after)
    return before+sep+after
def generate(reverse=False):
    result=['-- Name-only migration. Preserve data/types/defaults/indexes. Database: classhub_db.']
    for old in tables:
        current=tables[old] if reverse else old
        for constraint in constraints(old):
            name=re.match(r'CONSTRAINT `([^`]+)`',constraint)[1]
            kind='FOREIGN KEY' if ' FOREIGN KEY ' in constraint else 'CONSTRAINT'
            result.append(f'ALTER TABLE `{current}` DROP {kind} `{name}`;')
    for old in tables:
        current=tables[old] if reverse else old
        for col,new in columns[old].items():
            definition=re.search(r'^  `'+re.escape(col)+r'` (.*?)(?:,)?$',schema[old]['ddl'],re.M)[1].rstrip(',')
            src,dest=(new,col) if reverse else (col,new)
            result.append(f'ALTER TABLE `{current}` CHANGE COLUMN `{src}` `{dest}` {definition};')
    pairs=[f'`{new if reverse else old}` TO `{old if reverse else new}`' for old,new in tables.items() if old!=new]
    result.append('RENAME TABLE '+', '.join(pairs)+';')
    for old in tables:
        current=old if reverse else tables[old]
        for constraint in constraints(old):
            result.append(f'ALTER TABLE `{current}` ADD '+(constraint if reverse else translate_constraint(constraint,old))+';')
    return '\n'.join(result)+'\n'
docs=root.parents[1]/'docs/database'
docs.mkdir(parents=True,exist_ok=True)
(docs/'rename-to-english.sql').write_text(generate(),encoding='utf-8')
(docs/'rollback-english-names.sql').write_text(generate(True),encoding='utf-8')
mapping=['# Database English names','', 'Name-only changes. Status values and API payloads remain unchanged.','', '| Previous table | New table | Column changes |','| --- | --- | --- |']
mapping += [f'| `{old}` | `{new}` | '+', '.join(f'`{a}` → `{b}`' for a,b in columns[old].items())+' |' for old,new in tables.items()]
(docs/'english-names.md').write_text('\n'.join(mapping)+'\n',encoding='utf-8')
stage=root/'backend'
shutil.copytree(source,stage,dirs_exist_ok=True,ignore=shutil.ignore_patterns('bin','.git'))
classes={'cau_hinh_ca_hoc':'CauHinhCaHoc','nhat_ky_he_thong':'NhatKyHeThong','phieu_muon':'PhieuMuon','phong_hoc':'PhongHoc','tai_khoan':'TaiKhoan','thiet_bi':'ThietBi','thiet_bi_iot':'ThietBiIot','toa_nha':'ToaNha'}
changes=[]
for old,cls in classes.items():
    relative=f'Models/{cls}.cs';p=stage/relative;s=p.read_text(encoding='utf-8-sig')
    s=s.replace(f'[Table("{old}")]',f'[Table("{tables[old]}")]')
    for a,b in columns[old].items():s=s.replace(f'[Column("{a}")]',f'[Column("{b}")]')
    p.write_text(s,encoding='utf-8');changes.append(relative)
p=stage/'Data/AppDbContext.cs';s=p.read_text(encoding='utf-8-sig')
for old,new in tables.items():s=s.replace(f'.ToTable("{old}")',f'.ToTable("{new}")')
mappingcode='\n            // English physical names; retain CLR names and API contracts for compatibility.\n'
for old,cls in classes.items():
    for a,b in columns[old].items():mappingcode+=f'            modelBuilder.Entity<{cls}>().Property(e => e.{a}).HasColumnName("{b}");\n'
s=s.replace('            ConfigureAuditLogs(modelBuilder);','            ConfigureAuditLogs(modelBuilder);\n'+mappingcode)
p.write_text(s,encoding='utf-8');changes.append('Data/AppDbContext.cs')
# Update the unused future snapshot model/mapping without creating its table.
p=stage/'Models/PhieuMuonThietBi.cs';s=p.read_text(encoding='utf-8-sig').replace('[Table("phieu_muon_thiet_bi")]','[Table("borrowing_equipment")]')
for a,b in {'phieu_muon_id':'session_id','thiet_bi_id':'equipment_id','ten_thiet_bi':'name','so_luong':'quantity','tinh_trang_du_kien':'expected_condition'}.items():
    s=s.replace(f'        public ',f'        public ',1)
    s=re.sub(r'(        public [^\n]+\b'+a+r' \{)',f'        [Column("{b}")]\n'+r'\1',s)
p.write_text(s,encoding='utf-8');changes.append('Models/PhieuMuonThietBi.cs')
p=stage/'Data/AppDbContext.cs';s=p.read_text(encoding='utf-8').replace('entity.ToTable("phieu_muon_thiet_bi", table =>','entity.ToTable("borrowing_equipment", table =>').replace('"so_luong > 0"','"quantity > 0"');p.write_text(s,encoding='utf-8')
manifest={p:hashlib.sha256((source/p).read_bytes()).hexdigest() for p in changes}
(root/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
(root/'mapping.json').write_text(json.dumps({'tables':tables,'columns':columns}),encoding='utf-8')
print('Prepared forward/rollback SQL and backend mapping for ten live tables.')
