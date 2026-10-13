using ClassHub_API.Data;
using Microsoft.EntityFrameworkCore;
using MySqlConnector;
using System.Text.Json;

namespace ClassHub_API;
public static class MappingCheck
{
    public static async Task Main()
    {
        var config = new ConfigurationBuilder().AddJsonFile("C:/Users/edoga/AppData/Roaming/Microsoft/UserSecrets/8440d348-7540-4d65-b3c0-00df83ab0560/secrets.json").Build();
        var connectionString = config.GetConnectionString("DefaultConnection")!;
        await using var context = new AppDbContext(new DbContextOptionsBuilder<AppDbContext>()
            .UseMySql(connectionString, ServerVersion.AutoDetect(connectionString)).Options);
        await using var connection = new MySqlConnection(connectionString);
        await connection.OpenAsync();
        foreach (var entity in context.Model.GetEntityTypes())
        {
            var table=entity.GetTableName()!;
            if (table == "borrowing_equipment") continue; // Not implemented in the existing database.
            var store=Microsoft.EntityFrameworkCore.Metadata.StoreObjectIdentifier.Table(table,entity.GetSchema());
            var columns=entity.GetProperties().Select(p => "`"+p.GetColumnName(store)+"`");
            await using var command = new MySqlCommand("SELECT "+string.Join(",",columns)+" FROM `"+table+"` LIMIT 0",connection);
            await command.ExecuteNonQueryAsync();
            Console.WriteLine("Mapped columns verified: "+table);
        }
        await context.phieu_muon.AsNoTracking().Include(s => s.MaPhongNavigation)
            .Include(s => s.MaSvNavigation).Include(s => s.MaSvTraNavigation).Include(s => s.MaSvUyQuyenNavigation).Take(1).ToListAsync();
        await context.phong_hoc.AsNoTracking().Include(r => r.ThietBis).Include(r => r.ThietBiIots)
            .Include(r => r.MaToaNhaNavigation).Take(1).ToListAsync();
        await context.IotNodes.AsNoTracking().Take(1).ToListAsync();
        await context.IotSensors.AsNoTracking().Take(1).ToListAsync();
        Console.WriteLine("EF read queries and relationships verified; no data written.");
    }
}
