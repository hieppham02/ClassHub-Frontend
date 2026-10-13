from pathlib import Path
import json
root=Path('.codex-temp/assets/backend')
p=root/'Models/ThietBi.cs'
s=p.read_text(encoding='utf-8').replace('[Column("catalog_code"), MaxLength(36)]', '[Column("catalog_id")] public int CatalogId { get; set; }\n        [ForeignKey(nameof(CatalogId))] public EquipmentCatalog Catalog { get; set; } = null!;\n        [Column("catalog_code"), MaxLength(36)]')
p.write_text(s,encoding='utf-8')
p=root/'Data/AppDbContext.cs'
s=p.read_text(encoding='utf-8').replace('public DbSet<ThietBi> thiet_bi', 'public DbSet<EquipmentCatalog> EquipmentCatalogs { get; set; } = null!;\n        public DbSet<ThietBi> thiet_bi')
s=s.replace('base.OnModelCreating(modelBuilder);','base.OnModelCreating(modelBuilder);\n            modelBuilder.Entity<ThietBi>().HasOne(e=>e.Catalog).WithMany().HasForeignKey(e=>e.CatalogId).OnDelete(DeleteBehavior.Restrict);')
p.write_text(s,encoding='utf-8')
p=root/'Models/AssetRequests.cs'
s=p.read_text(encoding='utf-8').replace('public class AssetReceiptRequest\n{','public class AssetReceiptRequest\n{\n    public int? CatalogId { get; set; }')
p.write_text(s,encoding='utf-8')
p=root/'Controllers/AssetsController.cs'
s=p.read_text(encoding='utf-8').replace('e.CatalogCode, e.Version','e.CatalogCode, e.CatalogId, e.Version')
s=s.replace('return Ok(new { rooms, equipment=equipment.Select(Item),', 'var catalogs=await context.EquipmentCatalogs.AsNoTracking().OrderBy(c=>c.Name).ToListAsync();\n        return Ok(new { rooms, catalogs, equipment=equipment.Select(Item),')
anchor='        var item=new ThietBi { ten_thiet_bi=request.Name.Trim()'
start=s.index(anchor)
end=s.index('        try {',start)
s=s[:start]+'''        await using var tx=await context.Database.BeginTransactionAsync(IsolationLevel.Serializable);
        EquipmentCatalog? catalog;
        if(request.CatalogId.HasValue) {
            catalog=(await context.EquipmentCatalogs.FromSqlInterpolated($"SELECT * FROM equipment_catalog WHERE id={request.CatalogId.Value} FOR UPDATE").ToListAsync()).FirstOrDefault();
            if(catalog==null) return NotFound();
            if(!catalog.Enabled || catalog.TrackingMode!=request.TrackingMode) return Conflict(new {message="Danh mục ngừng sử dụng hoặc cách quản lý không khớp."});
        } else {
            catalog=await context.EquipmentCatalogs.FirstOrDefaultAsync(c=>c.Name==request.Name.Trim() && c.Category==request.Category.Trim() && c.TrackingMode==request.TrackingMode && c.UsageScope=="ROOM" && c.Enabled);
            if(catalog==null) {catalog=new EquipmentCatalog {Name=request.Name.Trim(),Category=request.Category.Trim(),TrackingMode=request.TrackingMode};context.EquipmentCatalogs.Add(catalog);await context.SaveChangesAsync();}
        }
        var item=new ThietBi {ten_thiet_bi=catalog.Name,Category=catalog.Category,UsageScope=catalog.UsageScope,TrackingMode=catalog.TrackingMode,CatalogId=catalog.Id,CatalogCode=catalog.Code,
            so_luong=request.Quantity,tinh_trang="TOT",ghi_chu=request.Note?.Trim(),AssetCode=string.IsNullOrEmpty(code)?null:code,Version=1};
'''+s[end:]
s=s.replace('if(item.UsageScope!="ROOM" || item.TrackingMode!="BULK")', 'if(item.ma_phong!=null || item.TrackingMode!="BULK")')
s=s.replace('CatalogCode=source.CatalogCode, Version=1', 'CatalogCode=source.CatalogCode, CatalogId=source.CatalogId, Version=1')
p.write_text(s,encoding='utf-8')
p=Path('.codex-temp/assets/manifest.json')
files=json.loads(p.read_text())
files += ['Models/EquipmentCatalog.cs','Controllers/EquipmentCatalogController.cs']
p.write_text(json.dumps(files),encoding='utf-8')
