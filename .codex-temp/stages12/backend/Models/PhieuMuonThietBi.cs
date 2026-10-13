using System.ComponentModel.DataAnnotations;
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
