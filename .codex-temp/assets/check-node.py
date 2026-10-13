from pathlib import Path
p=Path('.codex-temp/assets/integration/Program.cs')
s=p.read_text(encoding='utf-8').replace('Check(power.GetProperty("state").GetString()=="UNKNOWN","stale current cannot imply operation");', 'Check(power.GetProperty("state").GetString()=="LOW" && !power.GetProperty("isFresh").GetBoolean(),"offline node retains last current reading");\n    await Json(await client.PatchAsJsonAsync($"admin/assets/nodes/{powerNodeId}/status",new {status="MAINT"}));\n    Check((await Overview()).GetProperty("nodes").EnumerateArray().First(n=>Id(n)==powerNodeId).GetProperty("status").GetString()=="MAINT","node maintenance is persisted and shown");\n    Check((await client.PatchAsJsonAsync($"admin/assets/nodes/{powerNodeId}/status",new {status="INVALID"})).StatusCode==HttpStatusCode.BadRequest,"invalid node mode rejected");\n    await Json(await client.PatchAsJsonAsync($"admin/assets/nodes/{powerNodeId}/status",new {status="ACTIVE"}));\n    Check((await Overview()).GetProperty("nodes").EnumerateArray().First(n=>Id(n)==powerNodeId).GetProperty("status").GetString()=="OFFLINE","resuming node does not fabricate online connectivity");')
p.write_text(s,encoding='utf-8')
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8').replace("{{ node.status==='ONLINE' ? 'Online' : 'Mất kết nối' }}", "{{ node.status==='MAINT' ? 'Bảo trì' : node.status==='ONLINE' ? 'Trực tuyến' : 'Ngoại tuyến' }}")
s=s.replace('if (!busy.value && !modal.value)', 'if (!busy.value && !modal.value && !editingNode.value)')
p.write_text(s,encoding='utf-8')
