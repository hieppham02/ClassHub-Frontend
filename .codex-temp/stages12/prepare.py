from pathlib import Path
import shutil, hashlib, json
task = Path(__file__).resolve().parent
source = task.parents[2] / 'Backend/ClassHub-API/ClassHub-API'
stage = task / 'backend'
shutil.copytree(source, stage, dirs_exist_ok=True, ignore=shutil.ignore_patterns('bin','.git'))
changes = ['Controllers/OperationsController.cs','Services/BackgroundServices.cs','Controllers/RoomsController.cs','DTOs/DatPhongDTO.cs','Controllers/BookingController.cs']
hashes = {p: hashlib.sha256((source/p).read_bytes()).hexdigest() if (source/p).exists() else None for p in changes}
shutil.copyfile(task/'OperationsController.cs',stage/changes[0])
p=stage/changes[1]
s=p.read_text(encoding='utf-8-sig')
start=s.index('                    if (isLocked && borrowingSession.trang_thai == "RETURNING")')
end=s.index('\n                }\n\n                await dbContext.SaveChangesAsync();',start)
s=s[:start]+'''                    // A locked cabinet does not prove the equipment was returned.
                    // Keep RETURNING until an administrator verifies the contents.
'''+s[end:]
p.write_text(s,encoding='utf-8')
p=stage/changes[2]; s=p.read_text(encoding='utf-8-sig')
s=s.replace('                    tone = "from-blue-600 to-cyan-500"', '''                    equipmentDetails = room.ThietBis.OrderBy(e => e.id)
                        .Select(e => new { e.id, name = e.ten_thiet_bi, quantity = e.so_luong,
                            condition = e.tinh_trang, note = e.ghi_chu }).ToList(),
                    tone = "from-blue-600 to-cyan-500"''')
p.write_text(s,encoding='utf-8')
p=stage/changes[3]; s=p.read_text(encoding='utf-8-sig').replace('        public string VaiTro { get; set; }\n','');p.write_text(s,encoding='utf-8')
p=stage/changes[4]; s=p.read_text(encoding='utf-8-sig')
s=s.replace('            DateTime now = DateTime.Now;\n            string newOtp', '''            if (await _context.thiet_bi.AnyAsync(e => e.ma_phong == requestedRoomId
                && (e.tinh_trang != "TOT" || e.so_luong <= 0)))
                return BadRequest(new { message = "Bộ thiết bị của phòng có thiết bị hỏng hoặc cần bảo trì. Vui lòng liên hệ quản trị viên." });

            DateTime now = DateTime.Now;
            string newOtp''',1)
s=s.replace('            bool isFirstReturnRequest = borrowingSession.trang_thai != "RETURNING";', '''            if (borrowingSession.trang_thai == "PENDING")
                return Conflict(new { message = "Phiếu chưa nhận thiết bị; không thể yêu cầu trả." });

            bool isFirstReturnRequest = borrowingSession.trang_thai != "RETURNING";''')
p.write_text(s,encoding='utf-8')
(task/'manifest.json').write_text(json.dumps(hashes),encoding='utf-8')
print('Prepared four backend files; database unchanged.')
