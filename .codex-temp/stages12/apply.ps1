$ErrorActionPreference = 'Stop'
$taskRoot = 'E:\EAUT\Khoi_nghiep_sang_tao\ClassHub\Frontend\.codex-temp\stages12'
$backendRoot = 'E:\EAUT\Khoi_nghiep_sang_tao\ClassHub\Backend\ClassHub-API\ClassHub-API'
$manifest = Get-Content -LiteralPath (Join-Path $taskRoot 'manifest.json') -Raw | ConvertFrom-Json
foreach ($entry in $manifest.PSObject.Properties) {
    $targetFile = Join-Path $backendRoot $entry.Name
    if ($null -eq $entry.Value) {
        if (Test-Path -LiteralPath $targetFile) { throw "New file already exists: $($entry.Name)" }
    } elseif ((Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
        throw "Source changed since preparation: $($entry.Name)"
    }
}
foreach ($entry in $manifest.PSObject.Properties) {
    Copy-Item -LiteralPath (Join-Path (Join-Path $taskRoot 'backend') $entry.Name) -Destination (Join-Path $backendRoot $entry.Name)
}
Write-Output 'Applied five backend files. No database commands executed.'
