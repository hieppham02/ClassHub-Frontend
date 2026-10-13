from pathlib import Path
import json

base=Path(r'E:/EAUT/Khoi_nghiep_sang_tao/ClassHub/Backend/ClassHub-API/ClassHub-API')
stage=Path('.codex-temp/assets/backend')
manifest=[]
def write(relative,text):
    path=stage/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    manifest.append(relative)
def edit(relative,old,new):
    path=stage/relative
    text=path.read_text(encoding='utf-8') if path.exists() else (base/relative).read_text(encoding='utf-8-sig')
    assert old in text,relative
    write(relative,text.replace(old,new))

model='Models/ThietBi.cs'
edit(model,'        [ForeignKey("ma_phong")]', '''        [Column("category"), MaxLength(50)] public string Category { get; set; } = "Khác";
        [Column("usage_scope"), MaxLength(20)] public string UsageScope { get; set; } = "CABINET";
        [Column("tracking_mode"), MaxLength(20)] public string TrackingMode { get; set; } = "BULK";
        [Column("asset_code"), MaxLength(80)] public string? AssetCode { get; set; }
        [Column("catalog_code"), MaxLength(36)] public string CatalogCode { get; set; } = Guid.NewGuid().ToString();
        [Column("version")] public int Version { get; set; } = 1;

        [ForeignKey("ma_phong")]''')
edit('Controllers/BookingController.cs','e.ma_phong == requestedRoomId\n                &&','e.ma_phong == requestedRoomId && e.UsageScope == "CABINET"\n                &&')
edit('Controllers/RoomsController.cs','equipment = room.ThietBis\n','equipment = room.ThietBis.Where(e => e.UsageScope == "CABINET" && e.so_luong > 0)\n')
edit('Controllers/RoomsController.cs','equipmentDetails = room.ThietBis.OrderBy','equipmentDetails = room.ThietBis.Where(e => e.UsageScope == "CABINET" && e.so_luong > 0).OrderBy')
edit('Controllers/OperationsController.cs','context.thiet_bi.AsNoTracking()\n','context.thiet_bi.AsNoTracking().Where(e => e.UsageScope == "CABINET" && e.so_luong > 0)\n')
edit('Controllers/OperationsController.cs','        item.so_luong = request.Quantity;', '''        if (request.Quantity != item.so_luong)
            return Conflict(new { message = "Số lượng chỉ thay đổi qua nhập kho, phân bổ hoặc kiểm kê tài sản." });
        if (item.UsageScope != "CABINET")
            return Conflict(new { message = "Cập nhật tài sản phòng qua trang Quản lý tài sản." });
        item.Version++;''')
for folder,name in [('Controllers','AssetsController.cs'),('Models','AssetRequests.cs')]:
    write(folder+'/'+name,(Path('.codex-temp/assets')/name).read_text(encoding='utf-8'))
# Preserve all current EF mapping, only prevent room deletion from cascading asset loss.
text=(base/'Data/AppDbContext.cs').read_text(encoding='utf-8-sig')
start=text.index('private static void ConfigureEquipment')
end=text.index('private static void ',start+len('private static void '))
section=text[start:end]
assert 'DeleteBehavior.Cascade' in section
write('Data/AppDbContext.cs',text[:start]+section.replace('DeleteBehavior.Cascade','DeleteBehavior.Restrict')+text[end:])
Path('.codex-temp/assets/manifest.json').write_text(json.dumps(sorted(set(manifest))),encoding='utf-8')
print('Staged backend files:', len(set(manifest)))
