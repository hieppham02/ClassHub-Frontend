from pathlib import Path
import shutil

workspace = Path(__file__).resolve().parents[2]
source = workspace.parent / 'Backend/ClassHub-API/ClassHub-API'
staged = Path(__file__).resolve().parent / 'backend'
shutil.copytree(source, staged, dirs_exist_ok=True, ignore=shutil.ignore_patterns('bin', '.git'))
shutil.copyfile(source / 'Data/AppDbContext.cs', staged.parent / 'AppDbContext.original.cs')

model = '''using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ClassHub_API.Models
{
    // Expected equipment snapshot, not proof of physical handover or return.
    [Table("phieu_muon_thiet_bi")]
    public class PhieuMuonThietBi
    {
        [Key]
        public int id { get; set; }
        public int phieu_muon_id { get; set; }
        public int? thiet_bi_id { get; set; }
        public string ten_thiet_bi { get; set; } = null!;
        public int so_luong { get; set; }
        public string tinh_trang_du_kien { get; set; } = null!;

        public virtual PhieuMuon PhieuMuonNavigation { get; set; } = null!;
        public virtual ThietBi? ThietBiNavigation { get; set; }
    }
}
'''
(staged / 'Models/PhieuMuonThietBi.cs').write_text(model, encoding='utf-8')
context = staged / 'Data/AppDbContext.cs'
text = context.read_text(encoding='utf-8-sig')
text = text.replace('        protected override void OnModelCreating',
    '        public DbSet<PhieuMuonThietBi> phieu_muon_thiet_bi { get; set; } = null!;\n\n        protected override void OnModelCreating', 1)
text = text.replace('            ConfigureAuditLogs(modelBuilder);',
    '            ConfigureBorrowingEquipment(modelBuilder);\n            ConfigureAuditLogs(modelBuilder);', 1)
mapping = '''        private static void ConfigureBorrowingEquipment(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<PhieuMuonThietBi>(entity =>
            {
                entity.ToTable("phieu_muon_thiet_bi", table =>
                    table.HasCheckConstraint("CK_chi_tiet_so_luong", "so_luong > 0"));
                entity.HasKey(item => item.id);
                entity.Property(item => item.ten_thiet_bi).HasMaxLength(100).IsRequired();
                entity.Property(item => item.tinh_trang_du_kien).HasMaxLength(50).IsRequired();
                entity.HasIndex(item => new { item.phieu_muon_id, item.thiet_bi_id })
                    .IsUnique().HasDatabaseName("UX_phieu_thiet_bi");
                entity.HasIndex(item => item.thiet_bi_id).HasDatabaseName("IX_chi_tiet_thiet_bi");
                entity.HasOne(item => item.PhieuMuonNavigation).WithMany()
                    .HasForeignKey(item => item.phieu_muon_id)
                    .OnDelete(DeleteBehavior.Restrict).HasConstraintName("FK_chi_tiet_phieu");
                entity.HasOne(item => item.ThietBiNavigation).WithMany()
                    .HasForeignKey(item => item.thiet_bi_id)
                    .OnDelete(DeleteBehavior.SetNull).HasConstraintName("FK_chi_tiet_thiet_bi");
            });
        }

'''
assert 'private static void ConfigureAuditLogs' in text
text = text.replace('        private static void ConfigureAuditLogs', mapping + '        private static void ConfigureAuditLogs', 1)
context.write_text(text, encoding='utf-8')
print('Prepared model and EF mapping in workspace; source backend unchanged.')
