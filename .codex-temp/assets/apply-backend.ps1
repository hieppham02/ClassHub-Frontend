$ErrorActionPreference = 'Stop'
$taskRoot = 'E:\EAUT\Khoi_nghiep_sang_tao\ClassHub\Frontend\.codex-temp\assets'
$backendRoot = 'E:\EAUT\Khoi_nghiep_sang_tao\ClassHub\Backend\ClassHub-API\ClassHub-API'
$files = Get-Content -LiteralPath "$taskRoot\manifest.json" -Raw | ConvertFrom-Json
foreach ($file in $files) {
    $target = [IO.Path]::GetFullPath((Join-Path $backendRoot $file))
    if (-not $target.StartsWith($backendRoot + '\')) { throw 'Unexpected backend path' }
    Copy-Item -LiteralPath (Join-Path "$taskRoot\backend" $file) -Destination $target -Force
}
Write-Output 'Applied asset feature backend files.'
