from pathlib import Path
import json
root=Path(__file__).resolve().parent
p=root/'backend/Data/AppDbContext.cs';s=p.read_text(encoding='utf-8')
s=s.replace('        protected override void OnModelCreating','        public DbSet<IotNode> IotNodes { get; set; } = null!;\n        public DbSet<IotSensor> IotSensors { get; set; } = null!;\n\n        protected override void OnModelCreating',1)
s=s.replace('            ConfigureAuditLogs(modelBuilder);','''            ConfigureAuditLogs(modelBuilder);
            modelBuilder.Entity<IotNode>().HasIndex(n => n.NodeCode).IsUnique();
            modelBuilder.Entity<IotNode>().HasOne(n => n.Room).WithMany()
                .HasForeignKey(n => n.RoomId).OnDelete(DeleteBehavior.Restrict);
            modelBuilder.Entity<IotSensor>().HasIndex(s => new { s.NodeId, s.BootId, s.Sequence }).IsUnique();
            modelBuilder.Entity<IotSensor>().HasIndex(s => new { s.NodeId, s.MeasuredAt });
            modelBuilder.Entity<IotSensor>().HasOne(s => s.Node).WithMany()
                .HasForeignKey(s => s.NodeId).OnDelete(DeleteBehavior.Restrict);''',1)
p.write_text(s,encoding='utf-8')
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
for name in ['Models/IotNode.cs','Models/IotSensor.cs']:manifest[name]=None
(root/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
