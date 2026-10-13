using System.Text.Json;
var input = JsonSerializer.Deserialize<string[]>(Console.In.ReadToEnd())!;
if (args[0] == "hash")
    Console.Write(JsonSerializer.Serialize(input.Select(password => BCrypt.Net.BCrypt.HashPassword(password, 11)).ToArray()));
else
    Console.Write(JsonSerializer.Serialize(input.Select(hash => BCrypt.Net.BCrypt.Verify("123456", hash)).ToArray()));
