using System.Net;
using System.Net.Http.Json;
using System.Security.Claims;
using System.Text.Encodings.Web;
using System.Text.Json;
using ClassHub_API.Controllers;
using ClassHub_API.Data;
using Microsoft.AspNetCore.Authentication;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using MySqlConnector;

var database = Environment.GetEnvironmentVariable("CLASSHUB_CORRIDOR_TEST_DB");
if (database != "classhub_corridor_check") throw new Exception("Unsafe test database.");
var secrets = JsonDocument.Parse(File.ReadAllText(@"C:\Users\edoga\AppData\Roaming\Microsoft\UserSecrets\8440d348-7540-4d65-b3c0-00df83ab0560\secrets.json"));
var connection = secrets.RootElement.TryGetProperty("ConnectionStrings:DefaultConnection", out var flat) ? flat.GetString()! : secrets.RootElement.GetProperty("ConnectionStrings").GetProperty("DefaultConnection").GetString()!;
var cs = new MySqlConnectionStringBuilder(connection) { Database = database };
var builder = WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();
builder.Services.AddDbContext<AppDbContext>(o => o.UseMySql(cs.ConnectionString, ServerVersion.AutoDetect(cs.ConnectionString)));
builder.Services.AddControllers().AddApplicationPart(typeof(DamageReportsController).Assembly);
builder.Services.AddAuthentication("Test").AddScheme<AuthenticationSchemeOptions, TestAuthentication>("Test", _ => {});
builder.Services.AddAuthorization();
var app = builder.Build(); app.UseAuthentication(); app.UseAuthorization(); app.MapControllers();
app.Urls.Add("http://127.0.0.1:5299"); await app.StartAsync();
using var client = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:5299/api/") };
int passed = 0;
void Check(bool value, string label) { if (!value) throw new Exception(label); passed++; Console.WriteLine("PASS: " + label); }
void Role(string? role) { client.DefaultRequestHeaders.Remove("X-Test-Role"); if (role != null) client.DefaultRequestHeaders.Add("X-Test-Role", role); }
try {
    Check((await client.PostAsJsonAsync("damage-reports", new {})).StatusCode == HttpStatusCode.Unauthorized, "anonymous cannot report");
    Role("SINHVIEN");
    Check((await client.GetAsync("damage-reports")).StatusCode == HttpStatusCode.Forbidden, "student cannot read admin reports");
    Check((await client.PatchAsJsonAsync("damage-reports/1/resolve", new { note = "Đã sửa" })).StatusCode == HttpStatusCode.Forbidden, "student cannot resolve reports");
    Check((await client.PostAsJsonAsync("damage-reports", new { roomId = "unknown", equipmentName = "Ổ điện", description = "Ổ điện không hoạt động" })).StatusCode == HttpStatusCode.BadRequest, "unknown location rejected");
    var locations = await client.GetFromJsonAsync<JsonElement>("rooms/get-rooms");
    var corridors = locations.EnumerateArray().Where(r => r.GetProperty("locationType").GetString() == "CORRIDOR").ToArray();
    Check(corridors.GroupBy(r => (r.GetProperty("buildingId").GetString(), r.GetProperty("floorNum").GetInt32())).All(g => g.Count() == 1), "backend returns one corridor cabinet per floor");
    Check(corridors.All(r => r.GetProperty("name").GetString() == "Tủ tự do"), "corridor names remain Tủ tự do");
    var standards = locations.EnumerateArray().Where(r => r.GetProperty("id").GetString()!.StartsWith("STANDARD-")).ToArray();
    Check(standards.Length == corridors.Length * 5 && standards.GroupBy(r => (r.GetProperty("buildingId").GetString(), r.GetProperty("floorNum").GetInt32())).All(g => g.Count() == 5), "backend returns five additional ordinary cabinets per floor");
    Check(standards.All(r => r.GetProperty("hasCabinet").GetBoolean() && r.GetProperty("locationType").GetString() == "ROOM"), "ordinary cabinets linked to backend borrowing locations");
    Check(standards.All(r => System.Text.RegularExpressions.Regex.IsMatch(r.GetProperty("name").GetString()!, $"^{r.GetProperty("buildingId").GetString()}-{r.GetProperty("floorNum").GetInt32()}[0-9]{{2}}$")), "ordinary cabinets follow building-floor-room naming");
    Check(locations.EnumerateArray().Where(r => r.GetProperty("locationType").GetString() == "ROOM").GroupBy(r => (r.GetProperty("buildingId").GetString(), r.GetProperty("name").GetString())).All(g => g.Count() == 1), "room names do not collide with existing examples");
    var corridor = locations.EnumerateArray().First(r => r.GetProperty("locationType").GetString() == "CORRIDOR");
    var roomId = corridor.GetProperty("id").GetString();
    Check(corridor.GetProperty("isOnline").GetBoolean() == false, "new corridor cabinet stays offline");
    Check((await client.PostAsJsonAsync("damage-reports", new { roomId, equipmentName = "Ổ điện", description = "Ngắn" })).StatusCode == HttpStatusCode.BadRequest, "short description rejected");
    var created = await client.PostAsJsonAsync("damage-reports", new { roomId, equipmentName = "Ổ điện", description = "Ổ điện bị gãy chân cắm" });
    Check(created.StatusCode == HttpStatusCode.Created, "student can report an offline corridor cabinet");
    int id = (await created.Content.ReadFromJsonAsync<JsonElement>()).GetProperty("id").GetInt32();
    Role("ADMIN");
    var reports = await client.GetFromJsonAsync<JsonElement>("damage-reports");
    Check(reports.EnumerateArray().Any(r => r.GetProperty("id").GetInt32() == id && r.GetProperty("roomId").GetString() == roomId && r.GetProperty("status").GetString() == "PENDING"), "admin sees report at correct location");
    Check((await client.PatchAsJsonAsync($"damage-reports/{id}/resolve", new { note = "Đã thay ổ điện" })).StatusCode == HttpStatusCode.OK, "admin resolves with result");
    reports = await client.GetFromJsonAsync<JsonElement>("damage-reports");
    Check(reports.EnumerateArray().First(r => r.GetProperty("id").GetInt32() == id).GetProperty("status").GetString() == "RESOLVED", "resolved status persists");
    Check((await client.PatchAsJsonAsync($"damage-reports/{id}/resolve", new { note = "Đã thay ổ điện" })).StatusCode == HttpStatusCode.Conflict, "duplicate resolution rejected");
    var overview = await client.GetFromJsonAsync<JsonElement>("admin/assets");
    Check(overview.GetProperty("rooms").EnumerateArray().Any(r => r.GetProperty("id").GetString() == roomId), "corridor available in admin assets selector");
    Console.WriteLine($"Completed {passed} integration checks.");
} catch (Exception ex) {
    var message = ex.Message.Replace(cs.ConnectionString, "[connection]");
    if (!string.IsNullOrEmpty(cs.Password)) message = message.Replace(cs.Password, "[password]");
    Console.WriteLine("FAIL: " + message); Environment.ExitCode = 1;
} finally { await app.StopAsync(); }

public class TestAuthentication(IOptionsMonitor<AuthenticationSchemeOptions> options, ILoggerFactory logger, UrlEncoder encoder)
    : AuthenticationHandler<AuthenticationSchemeOptions>(options, logger, encoder)
{
    protected override Task<AuthenticateResult> HandleAuthenticateAsync() {
        string role = Request.Headers["X-Test-Role"].ToString();
        if (string.IsNullOrWhiteSpace(role)) return Task.FromResult(AuthenticateResult.NoResult());
        var identity = new ClaimsIdentity([new Claim(ClaimTypes.NameIdentifier, "ADMIN01"), new Claim(ClaimTypes.Role, role)], "Test");
        return Task.FromResult(AuthenticateResult.Success(new AuthenticationTicket(new ClaimsPrincipal(identity), "Test")));
    }
}
