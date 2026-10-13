using ClassHub_API.Data;
using ClassHub_API.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;
using System.Security.Claims;
using System.Text.Json;

namespace ClassHub_API.Controllers;

[ApiController, Authorize, Route("api/damage-reports")]
public class DamageReportsController(AppDbContext context) : ControllerBase
{
    public class CreateRequest
    {
        [Required, StringLength(50)] public string RoomId { get; set; } = "";
        [Required, StringLength(100)] public string EquipmentName { get; set; } = "";
        [Required, StringLength(2000, MinimumLength = 10)] public string Description { get; set; } = "";
    }
    public class ResolveRequest
    {
        [Required, StringLength(1000, MinimumLength = 3)] public string Note { get; set; } = "";
    }
    public class ReportDetail
    {
        public string RoomId { get; set; } = "";
        public string EquipmentName { get; set; } = "";
        public string Description { get; set; } = "";
        public string Status { get; set; } = "PENDING";
        public string? ResolutionNote { get; set; }
        public string? ResolvedBy { get; set; }
        public DateTime? ResolvedAt { get; set; }
    }

    [HttpPost]
    public async Task<IActionResult> Create(CreateRequest request)
    {
        var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (userId == null) return Unauthorized();
        if (!await context.tai_khoan.AnyAsync(a => a.ma_sv == userId && a.trang_thai)) return Forbid();
        if (!await context.phong_hoc.AnyAsync(r => r.ma_phong == request.RoomId))
            return BadRequest(new { message = "Vị trí báo hỏng không tồn tại." });
        if (request.EquipmentName.Trim().Length == 0 || request.Description.Trim().Length < 10)
            return BadRequest(new { message = "Nhập tên thiết bị và mô tả ít nhất 10 ký tự." });
        var report = new NhatKyHeThong {
            ma_sv = userId, hanh_dong = "DAMAGE_REPORT", thoi_gian = DateTime.Now,
            chi_tiet = JsonSerializer.Serialize(new ReportDetail { RoomId = request.RoomId,
                EquipmentName = request.EquipmentName.Trim(), Description = request.Description.Trim() }),
            user_agent = "ClassHub Damage Reports"
        };
        context.nhat_ky_he_thong.Add(report);
        await context.SaveChangesAsync();
        return StatusCode(201, new { report.id, message = "Đã gửi báo cáo hỏng hóc cho quản trị viên." });
    }

    [HttpGet, Authorize(Roles = "ADMIN")]
    public async Task<IActionResult> List()
    {
        var reports = await context.nhat_ky_he_thong.AsNoTracking()
            .Where(r => r.hanh_dong == "DAMAGE_REPORT")
            .OrderByDescending(r => r.thoi_gian).ThenByDescending(r => r.id).ToListAsync();
        return Ok(reports.Select(r => {
            var detail = JsonSerializer.Deserialize<ReportDetail>(r.chi_tiet ?? "{}")!;
            return new { r.id, reporterId = r.ma_sv, createdAt = r.thoi_gian,
                detail.RoomId, detail.EquipmentName, detail.Description, detail.Status,
                detail.ResolutionNote, detail.ResolvedBy, detail.ResolvedAt };
        }));
    }

    [HttpPatch("{id:int}/resolve"), Authorize(Roles = "ADMIN")]
    public async Task<IActionResult> Resolve(int id, ResolveRequest request)
    {
        if (request.Note.Trim().Length < 3) return BadRequest(new { message = "Nhập kết quả xử lý ít nhất 3 ký tự." });
        await using var transaction = await context.Database.BeginTransactionAsync();
        var report = await context.nhat_ky_he_thong
            .FromSqlInterpolated($"SELECT * FROM audit_log WHERE id={id} FOR UPDATE").FirstOrDefaultAsync();
        if (report == null || report.hanh_dong != "DAMAGE_REPORT") return NotFound();
        var detail = JsonSerializer.Deserialize<ReportDetail>(report.chi_tiet ?? "{}")!;
        if (detail.Status == "RESOLVED") return Conflict(new { message = "Báo cáo đã được xử lý." });
        detail.Status = "RESOLVED"; detail.ResolutionNote = request.Note.Trim();
        detail.ResolvedBy = User.FindFirstValue(ClaimTypes.NameIdentifier); detail.ResolvedAt = DateTime.Now;
        report.chi_tiet = JsonSerializer.Serialize(detail);
        context.nhat_ky_he_thong.Add(new NhatKyHeThong { ma_sv = detail.ResolvedBy,
            hanh_dong = "DAMAGE_RESOLVE", chi_tiet = JsonSerializer.Serialize(new { reportId = id, detail.RoomId, detail.ResolutionNote }),
            thoi_gian = DateTime.Now, user_agent = "ClassHub Damage Reports" });
        await context.SaveChangesAsync(); await transaction.CommitAsync();
        return Ok(new { message = "Đã đánh dấu báo cáo được xử lý." });
    }
}
