using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace ClassHub_API.Models
{
    [Table("equipment")]
    public class ThietBi
    {
        [Key]
        [Column("id")]
        public int id { get; set; }

        [Column("name")]
        public string ten_thiet_bi { get; set; } = null!;

        [Column("quantity")]
        public int so_luong { get; set; } = 1;

        [Column("condition")]
        public string tinh_trang { get; set; } = "TOT";

        [Column("note")]
        public string? ghi_chu { get; set; }

        [Column("room_id")]
        public string? ma_phong { get; set; }

        [ForeignKey("ma_phong")]
        public virtual PhongHoc? MaPhongNavigation { get; set; }
    }
}