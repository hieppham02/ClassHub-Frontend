using ClassHub_API.Data;
using ClassHub_API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Data;
using System.Security.Claims;
using System.Text.Json;

namespace ClassHub_API.Controllers;

[ApiController, Authorize(Roles = "ADMIN"), Route("api/admin/assets")]
public class AssetsController(AppDbContext context) : ControllerBase
{
    private static readonly string[] Conditions = ["TOT", "HONG", "DANG_BAO_TRI", "NGUNG_SU_DUNG"];
    private object Item(ThietBi e) => new { e.id, name=e.ten_thiet_bi, quantity=e.so_luong, condition=e.tinh_trang,
        note=e.ghi_chu, roomId=e.ma_phong, e.Category, e.UsageScope, e.TrackingMode, e.AssetCode, e.CatalogCode, e.Version };

    [HttpGet]
    public async Task<IActionResult> Overview()
    {
        var rooms = await context.phong_hoc.AsNoTracking().Include(r=>r.MaToaNhaNavigation)
            .OrderBy(r=>r.ma_toa_nha).ThenBy(r=>r.tang).ThenBy(r=>r.ma_phong)
            .Select(r=> new { id=r.ma_phong, name=r.ten_phong, buildingId=r.ma_toa_nha,
                building=r.MaToaNhaNavigation!=null?r.MaToaNhaNavigation.ten_toa_nha:r.ma_toa_nha, floor=r.tang }).ToListAsync();
        var equipment = await context.thiet_bi.AsNoTracking().Where(e=>e.so_luong>0).OrderBy(e=>e.ten_thiet_bi).ThenBy(e=>e.id).ToListAsync();
        var nodes = await context.IotNodes.AsNoTracking().OrderBy(n=>n.RoomId).ToListAsync();
        var latest = await context.IotSensors.AsNoTracking().Where(s=>s.Id==context.IotSensors.Where(t=>t.NodeId==s.NodeId).OrderByDescending(t=>t.ReceivedAt).ThenByDescending(t=>t.Id).Select(t=>t.Id).FirstOrDefault()).Select(s=>new {s.NodeId,s.ReceivedAt,s.ReadingsJson}).ToListAsync();
        var now=DateTime.UtcNow;
        return Ok(new { rooms, equipment=equipment.Select(Item), nodes=nodes.Select(n=> {
            var measurement=latest.FirstOrDefault(s=>s.NodeId==n.Id);
            var last=n.LastSeenAt ?? measurement?.ReceivedAt;
            bool online=n.DataSource!="MOCK" && n.Status=="ONLINE" && last.HasValue
                && (now-DateTime.SpecifyKind(last.Value,DateTimeKind.Utc)).TotalSeconds<=Math.Max(90,n.PublishIntervalSeconds*3);
            return new { n.Id, n.NodeCode, n.RoomId, n.Name, n.DataSource, status=online?"ONLINE":"OFFLINE", lastSeenAt=last,
                n.PublishIntervalSeconds, readings=Readings(measurement?.ReadingsJson) };
        }) });
    }

    [HttpGet("nodes/{id:int}/history")]
    public async Task<IActionResult> NodeHistory(int id,[FromQuery] int hours=24)
    {
        if(hours<1 || hours>720) return BadRequest(new { message="Khoảng xem từ 1 đến 720 giờ." });
        var node=await context.IotNodes.AsNoTracking().FirstOrDefaultAsync(n=>n.Id==id);
        if(node==null) return NotFound();
        // Stored mock messages use the same contract as real telemetry, without fabricated online state.
        var anchor=node.DataSource=="MOCK" ? await context.IotSensors.Where(s=>s.NodeId==id).Select(s=>(DateTime?)s.ReceivedAt).MaxAsync() : DateTime.UtcNow;
        var cutoff=(anchor??DateTime.UtcNow).AddHours(-hours);
        var samples=await context.IotSensors.AsNoTracking().Where(s=>s.NodeId==id && s.ReceivedAt>=cutoff)
            .OrderByDescending(s=>s.ReceivedAt).ThenByDescending(s=>s.Id).Take(200).Select(s=>new {s.Id,s.MeasuredAt,s.ReceivedAt,s.ReadingsJson}).ToListAsync();
        return Ok(new { node.DataSource, samples=samples.OrderBy(s=>s.ReceivedAt).Select(s=>new {
            s.Id, measuredAt=s.MeasuredAt??s.ReceivedAt, s.ReceivedAt, readings=Readings(s.ReadingsJson) }) });
    }

    [HttpGet("history")]
    public async Task<IActionResult> History([FromQuery] int page=1,[FromQuery] string? roomId=null)
    {
        if(page<1) return BadRequest();
        var query=context.nhat_ky_he_thong.AsNoTracking().Where(l=>l.hanh_dong.StartsWith("ASSET_"));
        if(!string.IsNullOrWhiteSpace(roomId)) {
            string key=JsonSerializer.Serialize(roomId);
            query=query.Where(l=>l.chi_tiet!=null && (l.chi_tiet.Contains("\"fromRoomId\":"+key) || l.chi_tiet.Contains("\"toRoomId\":"+key)));
        }
        var count=await query.CountAsync();
        var logs=await query.OrderByDescending(l=>l.id).Skip((page-1)*20).Take(20)
            .Select(l=>new { l.id, action=l.hanh_dong, actor=l.TaiKhoanNavigation!=null?l.TaiKhoanNavigation.ho_ten:l.ma_sv,
                createdAt=l.thoi_gian, details=l.chi_tiet }).ToListAsync();
        return Ok(new { items=logs, totalItems=count, page, pageSize=20 });
    }

    [HttpPost("receipts")]
    public async Task<IActionResult> Receipt(AssetReceiptRequest request)
    {
        if(string.IsNullOrWhiteSpace(request.Name) || string.IsNullOrWhiteSpace(request.Category) ||
            !new[]{"BULK","INDIVIDUAL"}.Contains(request.TrackingMode)) return BadRequest(new { message="Tên, loại tài sản hoặc cách quản lý không hợp lệ." });
        var code=request.AssetCode?.Trim();
        if(request.TrackingMode=="INDIVIDUAL" && (request.Quantity!=1 || string.IsNullOrWhiteSpace(code)))
            return BadRequest(new { message="Tài sản quản lý riêng phải có mã và số lượng bằng 1." });
        if(request.TrackingMode=="BULK" && !string.IsNullOrEmpty(code)) return BadRequest(new { message="Mã tài sản chỉ áp dụng cho quản lý từng chiếc." });
        var item=new ThietBi { ten_thiet_bi=request.Name.Trim(), so_luong=request.Quantity, tinh_trang="TOT", ghi_chu=request.Note?.Trim(),
            Category=request.Category.Trim(), UsageScope="ROOM", TrackingMode=request.TrackingMode, AssetCode=string.IsNullOrEmpty(code)?null:code, CatalogCode=Guid.NewGuid().ToString(), Version=1 };
        await using var tx=await context.Database.BeginTransactionAsync();
        try {
            context.thiet_bi.Add(item); await context.SaveChangesAsync();
            Log("RECEIPT",item,null,null,item.so_luong,0,item.so_luong,item.tinh_trang,request.Note);
            await context.SaveChangesAsync(); await tx.CommitAsync(); return Ok(Item(item));
        } catch(DbUpdateException) { return Conflict(new { message="Mã tài sản đã tồn tại hoặc dữ liệu thay đổi. Vui lòng tải lại." }); }
    }

    [HttpPatch("{id:int}/condition")]
    public async Task<IActionResult> Condition(int id,AssetConditionRequest request)
    {
        if(!Conditions.Contains(request.Condition) || string.IsNullOrWhiteSpace(request.Note)) return BadRequest(new { message="Chọn tình trạng và nhập lý do cập nhật." });
        await using var tx=await context.Database.BeginTransactionAsync(IsolationLevel.Serializable);
        var item=await Locked(id);
        if(item==null) return NotFound();
        if(item.Version!=request.Version) return Conflict(new { message="Tài sản đã thay đổi. Vui lòng tải lại." });
        if(request.AffectedCount>item.so_luong || request.Condition==item.tinh_trang) return BadRequest(new { message="Số lượng ảnh hưởng hoặc tình trạng mới không hợp lệ." });
        var room=item.ma_phong; var oldCondition=item.tinh_trang; var original=item.so_luong;
        var target=Split(item,request.AffectedCount);
        target.tinh_trang=request.Condition; target.ghi_chu=request.Note.Trim();
        await context.SaveChangesAsync();
        Log("CONDITION",target,room,room,request.AffectedCount,original,original,oldCondition,request.Note);
        await context.SaveChangesAsync(); await tx.CommitAsync(); return Ok(new { message="Đã cập nhật tình trạng; tổng số tài sản được giữ nguyên." });
    }

    [HttpPost("{id:int}/move")]
    public async Task<IActionResult> Move(int id,AssetMoveRequest request)
    {
        if(string.IsNullOrWhiteSpace(request.Note) || !new[]{"ALLOCATE","RETURN","TRANSFER"}.Contains(request.Action)) return BadRequest(new { message="Chọn nghiệp vụ và nhập ghi chú." });
        await using var tx=await context.Database.BeginTransactionAsync(IsolationLevel.Serializable);
        var item=await Locked(id); if(item==null) return NotFound();
        if(item.Version!=request.Version) return Conflict(new { message="Tài sản đã thay đổi. Vui lòng tải lại." });
        if(item.UsageScope!="ROOM") return Conflict(new { message="Bộ thiết bị mượn trong tủ không được điều chuyển qua phân bổ tài sản phòng." });
        if(request.Quantity>item.so_luong) return BadRequest(new { message="Số lượng vượt số hiện có." });
        var target=request.Action=="RETURN"?null:request.TargetRoomId?.Trim();
        if(request.Action=="RETURN" && (item.ma_phong==null || !string.IsNullOrWhiteSpace(request.TargetRoomId))) return BadRequest(new { message="Thu hồi phải từ phòng về kho." });
        if(request.Action=="ALLOCATE" && (item.ma_phong!=null || item.tinh_trang!="TOT")) return BadRequest(new { message="Chỉ cấp tài sản sử dụng tốt từ kho." });
        if(request.Action=="TRANSFER" && (item.ma_phong==null || item.tinh_trang!="TOT")) return BadRequest(new { message="Chỉ điều chuyển tài sản sử dụng tốt giữa các phòng." });
        if(request.Action!="RETURN" && (string.IsNullOrWhiteSpace(target) || target==item.ma_phong || !await context.phong_hoc.AnyAsync(r=>r.ma_phong==target))) return BadRequest(new { message="Phòng nhận không hợp lệ." });
        var from=item.ma_phong; var original=item.so_luong;
        var destination=Split(item,request.Quantity); destination.ma_phong=target; destination.ghi_chu=request.Note.Trim();
        await context.SaveChangesAsync(); Log(request.Action,destination,from,target,request.Quantity,original,original,item.tinh_trang,request.Note);
        await context.SaveChangesAsync(); await tx.CommitAsync(); return Ok(new { message="Đã cập nhật vị trí tài sản và số lượng kho/phòng." });
    }

    [HttpPost("{id:int}/count")]
    public async Task<IActionResult> Count(int id,AssetCountRequest request)
    {
        if(string.IsNullOrWhiteSpace(request.Note)) return BadRequest(new { message="Cần lý do điều chỉnh kiểm kê." });
        await using var tx=await context.Database.BeginTransactionAsync(IsolationLevel.Serializable);
        var item=await Locked(id); if(item==null) return NotFound();
        if(item.Version!=request.Version) return Conflict(new { message="Tài sản đã thay đổi. Vui lòng tải lại." });
        if(item.UsageScope!="ROOM" || item.TrackingMode!="BULK") return BadRequest(new { message="Kiểm kê số lượng chỉ áp dụng cho tài sản phòng quản lý theo nhóm." });
        var before=item.so_luong; if(before==request.ActualCount) return BadRequest(new { message="Số lượng thực tế không thay đổi." });
        item.so_luong=request.ActualCount; item.Version++; item.ghi_chu=request.Note.Trim();
        Log("COUNT",item,item.ma_phong,item.ma_phong,Math.Abs(before-request.ActualCount),before,request.ActualCount,item.tinh_trang,request.Note);
        await context.SaveChangesAsync(); await tx.CommitAsync(); return Ok(new { message="Đã ghi nhận chênh lệch kiểm kê." });
    }

    private async Task<ThietBi?> Locked(int id) => (await context.thiet_bi.FromSqlInterpolated($"SELECT * FROM equipment WHERE id={id} FOR UPDATE").ToListAsync()).FirstOrDefault(e=>e.so_luong>0);
    private ThietBi Split(ThietBi source,int count)
    {
        source.Version++;
        if(count==source.so_luong) return source;
        if(source.TrackingMode=="INDIVIDUAL") throw new InvalidOperationException("Individual assets cannot split.");
        source.so_luong-=count;
        var target=new ThietBi { ten_thiet_bi=source.ten_thiet_bi, so_luong=count, tinh_trang=source.tinh_trang, ghi_chu=source.ghi_chu,
            ma_phong=source.ma_phong, Category=source.Category, UsageScope=source.UsageScope, TrackingMode=source.TrackingMode, CatalogCode=source.CatalogCode, Version=1 };
        context.thiet_bi.Add(target); return target;
    }
    private void Log(string action,ThietBi item,string? from,string? to,int count,int before,int after,string oldCondition,string? note)
        => context.nhat_ky_he_thong.Add(new NhatKyHeThong { ma_sv=User.FindFirstValue(ClaimTypes.NameIdentifier), hanh_dong="ASSET_"+action,
            chi_tiet=JsonSerializer.Serialize(new { assetId=item.id, name=item.ten_thiet_bi, assetCode=item.AssetCode, catalogCode=item.CatalogCode,
                fromRoomId=from, toRoomId=to, quantity=count, before, after, oldCondition, condition=item.tinh_trang, note=note?.Trim() }), thoi_gian=DateTime.Now, user_agent="ClassHub Assets" });
    private static JsonElement Readings(string? json) {
        try { return JsonSerializer.Deserialize<JsonElement>(json??"[]"); } catch(JsonException) { return JsonSerializer.Deserialize<JsonElement>("[]"); }
    }
}
