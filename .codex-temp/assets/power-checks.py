from pathlib import Path
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8').replace("name: 'Dòng điện'", "name: 'Dòng điện tổng phòng'")
p.write_text(s,encoding='utf-8')
p=Path('.codex-temp/assets/integration/Program.cs')
s=p.read_text(encoding='utf-8')
anchor='    Console.WriteLine($"Completed {passed} integration checks against isolated database.");'
code='''    var powerNodeId=Id(node);
    var power=await Json(await client.GetAsync($"admin/assets/nodes/{powerNodeId}/power"));
    Check(power.GetProperty("state").GetString()=="UNKNOWN","stale current cannot imply operation");
    using(var scope=app.Services.CreateScope()) {
        var db=scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var room=node.GetProperty("roomId").GetString()!;
        db.phieu_muon.RemoveRange(await db.phieu_muon.Where(b=>b.ma_phong==room).ToListAsync());
        var now=DateTime.UtcNow;
        db.IotSensors.Add(new ClassHub_API.Models.IotSensor {NodeId=powerNodeId,BootId="power-test",Sequence=1,ReceivedAt=now,DataSource="MOCK",ReadingsJson="[{\\"metric\\":\\"current\\",\\"value\\":0.3,\\"quality\\":\\"GOOD\\"}]"});
        await db.SaveChangesAsync();
        power=await Json(await client.GetAsync($"admin/assets/nodes/{powerNodeId}/power"));
        Check(power.GetProperty("state").GetString()=="LOW","below 1A is low consumption");
        db.IotSensors.RemoveRange(await db.IotSensors.Where(t=>t.NodeId==powerNodeId && t.BootId=="power-test").ToListAsync());
        await db.SaveChangesAsync();
        for(int i=0;i<=14;i++) db.IotSensors.Add(new ClassHub_API.Models.IotSensor {NodeId=powerNodeId,BootId="power-test",Sequence=(ulong)(i+1),ReceivedAt=now.AddSeconds(-30*i),DataSource="MOCK",ReadingsJson="[{\\"metric\\":\\"current\\",\\"value\\":2,\\"quality\\":\\"GOOD\\"}]"});
        await db.SaveChangesAsync();
        power=await Json(await client.GetAsync($"admin/assets/nodes/{powerNodeId}/power"));
        Check(power.GetProperty("state").GetString()=="OUT_OF_SCHEDULE","continuous high current outside borrowing warns");
        db.phieu_muon.Add(new ClassHub_API.Models.PhieuMuon {ma_sv="ADMIN01",ma_phong=room,ca_muon=1,ngay_muon=now.AddHours(7).Date,thoi_gian_nhan=now.AddHours(7).AddMinutes(-10),trang_thai="IN_USE"});
        await db.SaveChangesAsync();
        power=await Json(await client.GetAsync($"admin/assets/nodes/{powerNodeId}/power"));
        Check(power.GetProperty("state").GetString()=="IN_USE","active borrowing suppresses outside schedule warning");
    }
'''
assert anchor in s
p.write_text(s.replace(anchor,code+anchor),encoding='utf-8')
