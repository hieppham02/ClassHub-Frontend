from pathlib import Path
p=Path('.codex-temp/assets/integration/Program.cs')
s=p.read_text(encoding='utf-8')
anchor='    var powerNodeId=Id(node);'
code='''    var serialCurrent=await GetItem(serialId);
    await Json(await client.PostAsJsonAsync($"admin/assets/{serialId}/room-quantity",new {actualCount=0,version=Version(serialCurrent),note="Return individual asset"}));
    serialCurrent=await GetItem(serialId);
    Check(Room(serialCurrent)==null && serialCurrent.GetProperty("assetCode").GetString()=="INTEGRATION-MC001","individual return preserves identity in warehouse");
    await Json(await client.PostAsJsonAsync($"admin/assets/{serialId}/count",new {actualCount=0,version=Version(serialCurrent),note="Remove retired individual asset"}));
    Check(!(await Overview()).GetProperty("equipment").EnumerateArray().Any(e=>Id(e)==serialId),"individual warehouse deletion records zero inventory");
'''
assert anchor in s
p.write_text(s.replace(anchor,code+anchor),encoding='utf-8')
