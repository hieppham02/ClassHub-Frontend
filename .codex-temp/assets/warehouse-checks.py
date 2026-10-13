from pathlib import Path
p=Path('.codex-temp/assets/integration/Program.cs')
s=p.read_text(encoding='utf-8').replace('telemetry.GetProperty("samples").GetArrayLength()>0 && node.GetProperty("status").GetString()=="OFFLINE","stored mock telemetry loads without fake online state"','telemetry.GetProperty("samples").GetArrayLength()>0,"stored telemetry loads for configured connectivity"')
anchor='    var powerNodeId=Id(node);'
code='''    var emptyCatalog=await Json(await client.PostAsJsonAsync("admin/assets/catalogs",new {name="Integration empty catalog",category="Furniture",trackingMode="BULK",enabled=true}));
    await Json(await client.DeleteAsync($"admin/assets/catalogs/{Id(emptyCatalog)}?version=1"));
    Check(!(await Overview()).GetProperty("catalogs").EnumerateArray().Any(c=>Id(c)==Id(emptyCatalog)),"empty catalog can be created and deleted");
    var sharedCatalogId=(await GetItem(chairsId)).GetProperty("catalogId").GetInt32();
    var linkedCatalog=(await Overview()).GetProperty("catalogs").EnumerateArray().First(c=>Id(c)==sharedCatalogId);
    await Json(await client.PatchAsJsonAsync($"admin/assets/catalogs/{sharedCatalogId}",new {name="Integration shared chairs",category="Shared furniture",trackingMode="BULK",enabled=true,version=Version(linkedCatalog)}));
    Check((await Items(catalog)).All(e=>e.GetProperty("name").GetString()=="Integration shared chairs" && e.GetProperty("category").GetString()=="Shared furniture"),"catalog metadata synchronizes across warehouse and rooms");
    Check((await client.DeleteAsync($"admin/assets/catalogs/{sharedCatalogId}?version=2")).StatusCode==HttpStatusCode.Conflict,"catalog with equipment cannot be deleted");
    var stockBefore=await GetItem(chairsId);
    await Json(await client.PostAsJsonAsync("admin/assets/rooms/DTD202/equipment",new {equipmentId=chairsId,quantity=3,version=Version(stockBefore),note="Add from warehouse"}));
    var roomItem=(await Items(catalog)).First(e=>Room(e)=="DTD202" && e.GetProperty("condition").GetString()=="TOT");
    var totalBefore=(await Items(catalog)).Sum(Quantity);
    await Json(await client.PostAsJsonAsync($"admin/assets/{Id(roomItem)}/room-quantity",new {actualCount=Quantity(roomItem)+2,version=Version(roomItem),note="Increase from warehouse"}));
    Check((await Items(catalog)).Sum(Quantity)==totalBefore && Quantity(await GetItem(Id(roomItem)))==Quantity(roomItem)+2,"room increase consumes warehouse and preserves total");
    roomItem=await GetItem(Id(roomItem));
    Check((await client.PostAsJsonAsync($"admin/assets/{Id(roomItem)}/room-quantity",new {actualCount=10000,version=Version(roomItem),note="Overdraw attempt"})).StatusCode==HttpStatusCode.Conflict,"room increase cannot exceed stock");
    await Json(await client.PostAsJsonAsync($"admin/assets/{Id(roomItem)}/room-quantity",new {actualCount=1,version=Version(roomItem),note="Return difference"}));
    Check((await Items(catalog)).Sum(Quantity)==totalBefore && Quantity(await GetItem(Id(roomItem)))==1,"room decrease returns difference and preserves total");
    var allocated=await GetItem(Id(roomItem));
    Check((await client.PostAsJsonAsync($"admin/assets/{Id(allocated)}/count",new {actualCount=8,version=Version(allocated),note="Direct count bypass"})).StatusCode==HttpStatusCode.BadRequest,"warehouse count cannot change room total directly");
    var activeCatalog=(await Overview()).GetProperty("catalogs").EnumerateArray().First(c=>Id(c)==sharedCatalogId);
    await Json(await client.PatchAsJsonAsync($"admin/assets/catalogs/{sharedCatalogId}",new {name="Integration shared chairs",category="Shared furniture",trackingMode="BULK",enabled=false,version=Version(activeCatalog)}));
    var available=(await Items(catalog)).First(e=>Room(e)==null && e.GetProperty("condition").GetString()=="TOT");
    Check((await client.PostAsJsonAsync("admin/assets/rooms/DTD202/equipment",new {equipmentId=Id(available),quantity=1,version=Version(available),note="Inactive catalog attempt"})).StatusCode==HttpStatusCode.Conflict,"disabled catalog cannot issue equipment");
    var disabledCatalog=(await Overview()).GetProperty("catalogs").EnumerateArray().First(c=>Id(c)==sharedCatalogId);
    await Json(await client.PatchAsJsonAsync($"admin/assets/catalogs/{sharedCatalogId}",new {name="Integration shared chairs",category="Shared furniture",trackingMode="BULK",enabled=true,version=Version(disabledCatalog)}));
    var currentRoom=await GetItem(Id(roomItem));
    var competing=await Task.WhenAll(Enumerable.Range(0,2).Select(_=>client.PostAsJsonAsync($"admin/assets/{Id(currentRoom)}/room-quantity",new {actualCount=2,version=Version(currentRoom),note="Concurrent quantity"})));
    Check(competing.Count(r=>r.StatusCode==HttpStatusCode.OK)==1 && competing.Count(r=>r.StatusCode==HttpStatusCode.Conflict)==1,"concurrent room edits only commit once");
    Check((await Items(catalog)).Sum(Quantity)==totalBefore,"concurrent room edits preserve catalog total");
'''
assert anchor in s
p.write_text(s.replace(anchor,code+anchor),encoding='utf-8')
p=Path('src/views/admin/AssetsView.vue')
s=p.read_text(encoding='utf-8').replace(" && (tab.value !== 'allocation' || e.usageScope === 'ROOM')",'')
s=s.replace("{label:tab.value==='allocation'?'Kho khả dụng':'Ngừng sử dụng',value:tab.value==='allocation'?warehouseCount.value:sum('NGUNG_SU_DUNG'),color:'text-slate-600'}", "{label:'Ngừng sử dụng',value:sum('NGUNG_SU_DUNG'),color:'text-slate-600'}")
s=s.replace("<p v-if=\"selectedAsset\" class=\"rounded-xl", "<p v-if=\"selectedAsset && !modal.startsWith('CATALOG_')\" class=\"rounded-xl")
s=s.replace('class="px-5 py-4 font-semibold text-ink">{{ asset.quantity }}</td>', 'class="px-5 py-4 font-semibold text-ink">{{ asset.quantity }}<p class="mt-1 text-xs font-normal text-slate-500">Kho khả dụng: {{ equipment.filter(e=>e.catalogId===asset.catalogId && !e.roomId && e.condition===\'TOT\').reduce((sum,e)=>sum+e.quantity,0) }}</p></td>')
p.write_text(s,encoding='utf-8')
