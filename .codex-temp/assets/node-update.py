from pathlib import Path
p=Path('.codex-temp/assets/backend/Controllers/AssetsController.cs')
s=p.read_text(encoding='utf-8')
s=s.replace('status=online?"ONLINE":"OFFLINE"','status=n.Status=="MAINT"?"MAINT":online?"ONLINE":"OFFLINE"')
s=s.replace('var latest=samples.FirstOrDefault();','var latest=samples.FirstOrDefault() ?? await context.IotSensors.AsNoTracking().Where(s=>s.NodeId==id).OrderByDescending(s=>s.ReceivedAt).ThenByDescending(s=>s.Id).Select(s=>new {s.ReceivedAt,s.ReadingsJson}).FirstOrDefaultAsync();')
s=s.replace('string state=!fresh || !amperes.HasValue ? "UNKNOWN"', 'string state=!amperes.HasValue ? "NO_DATA"')
anchor='    [HttpGet("nodes/{id:int}/power")]'
code='''    [HttpPatch("nodes/{id:int}/status")]
    public async Task<IActionResult> NodeStatus(int id,NodeStatusRequest request)
    {
        if(request.Status!="ACTIVE" && request.Status!="MAINT") return BadRequest(new {message="Chọn hoạt động hoặc bảo trì."});
        await using var tx=await context.Database.BeginTransactionAsync();
        var node=await context.IotNodes.FromSqlInterpolated($"SELECT * FROM iot_node WHERE id={id} FOR UPDATE").FirstOrDefaultAsync();
        if(node==null) return NotFound();
        var before=node.Status;
        node.Status=request.Status=="MAINT"?"MAINT":"OFFLINE";
        if(request.Status=="ACTIVE" && node.DataSource!="MOCK" && node.LastSeenAt.HasValue
            && (DateTime.UtcNow-node.LastSeenAt.Value).TotalSeconds<=Math.Max(90,node.PublishIntervalSeconds*3)) node.Status="ONLINE";
        context.nhat_ky_he_thong.Add(new NhatKyHeThong {ma_sv=User.FindFirstValue(ClaimTypes.NameIdentifier),hanh_dong="NODE_STATUS",
            chi_tiet=JsonSerializer.Serialize(new {nodeId=id,roomId=node.RoomId,before,after=node.Status}),thoi_gian=DateTime.Now,user_agent="ClassHub Nodes"});
        await context.SaveChangesAsync(); await tx.CommitAsync();
        return Ok(new {message="Đã cập nhật trạng thái node."});
    }

'''
s=s.replace(anchor,code+anchor)
p.write_text(s,encoding='utf-8')
p=Path('.codex-temp/assets/backend/Models/AssetRequests.cs')
s=p.read_text(encoding='utf-8')+'\npublic class NodeStatusRequest { [Required] public string Status { get; set; } = "ACTIVE"; }\n'
p.write_text(s,encoding='utf-8')
