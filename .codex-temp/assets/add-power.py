from pathlib import Path
p=Path('.codex-temp/assets/backend/Controllers/AssetsController.cs')
s=p.read_text(encoding='utf-8')
anchor='    [HttpGet("nodes/{id:int}/history")]'
code='''    [HttpGet("nodes/{id:int}/power")]
    public async Task<IActionResult> RoomPower(int id)
    {
        var node=await context.IotNodes.AsNoTracking().FirstOrDefaultAsync(n=>n.Id==id);
        if(node==null) return NotFound();
        var now=DateTime.UtcNow;
        var cutoff=now.AddMinutes(-10);
        var samples=await context.IotSensors.AsNoTracking()
            .Where(s=>s.NodeId==id && s.ReceivedAt>=cutoff && s.ReceivedAt<=now)
            .OrderByDescending(s=>s.ReceivedAt).ThenByDescending(s=>s.Id).Take(1000)
            .Select(s=>new {s.ReceivedAt,s.ReadingsJson}).ToListAsync();
        // Borrowing timestamps follow the existing Vietnam local-time convention.
        var localNow=now.AddHours(7);
        var sessions=await context.phieu_muon.AsNoTracking().Where(b=>b.ma_phong==node.RoomId
            && b.thoi_gian_nhan!=null && b.thoi_gian_nhan<=localNow
            && (b.thoi_gian_tra==null || b.thoi_gian_tra>=localNow.AddMinutes(-10))
            && b.trang_thai!="CANCELED" && b.trang_thai!="PENDING")
            .Select(b=>new {start=b.thoi_gian_nhan!.Value,end=b.thoi_gian_tra}).ToListAsync();
        bool InUse(DateTime utc)=>sessions.Any(b=>b.start<=utc.AddHours(7) && (b.end==null || b.end>utc.AddHours(7)));
        double? Current(string json) {
            var readings=Readings(json);
            if(readings.ValueKind!=JsonValueKind.Array) return null;
            foreach(var r in readings.EnumerateArray())
                if(r.TryGetProperty("metric",out var metric) && metric.GetString()=="current"
                    && r.TryGetProperty("quality",out var quality) && quality.GetString()=="GOOD"
                    && r.TryGetProperty("value",out var value) && value.TryGetDouble(out var number)
                    && double.IsFinite(number) && number>=0) return number;
            return null;
        }
        var latest=samples.FirstOrDefault();
        double? amperes=latest==null?null:Current(latest.ReadingsJson);
        int maxGap=Math.Max(90,node.PublishIntervalSeconds*3);
        bool fresh=latest!=null && (now-latest.ReceivedAt).TotalSeconds<=maxGap;
        bool borrowing=InUse(now);
        bool sustained=false;
        DateTime? since=null;
        if(fresh && amperes>=1 && !borrowing) {
            var previous=now;
            foreach(var sample in samples) {
                if((previous-sample.ReceivedAt).TotalSeconds>maxGap || Current(sample.ReadingsJson) is not double current || current<1 || InUse(sample.ReceivedAt)) break;
                since=sample.ReceivedAt; previous=sample.ReceivedAt;
            }
            sustained=since.HasValue && (latest!.ReceivedAt-since.Value).TotalMinutes>=5;
        }
        string state=!fresh || !amperes.HasValue ? "UNKNOWN" : amperes<1 ? "LOW" : borrowing ? "IN_USE" : sustained ? "OUT_OF_SCHEDULE" : "OBSERVING";
        return Ok(new {scope="ROOM_TOTAL",thresholdAmperes=1,requiredDurationMinutes=5,
            roomHasActiveBorrowing=borrowing,currentAmperes=amperes,isFresh=fresh,state,
            measuredAt=latest?.ReceivedAt,highConsumptionSince=since});
    }

'''
assert anchor in s
p.write_text(s.replace(anchor,code+anchor),encoding='utf-8')
