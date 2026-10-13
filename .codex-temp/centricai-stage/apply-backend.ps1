$ErrorActionPreference = 'Stop'
$stageRoot = 'E:\EAUT\Khoi_nghiep_sang_tao\ClassHub\Frontend\.codex-temp\centricai-stage'
$backendRoot = 'E:\EAUT\Khoi_nghiep_sang_tao\ClassHub\Backend\ClassHub-API\ClassHub-API'
$contextTarget = Join-Path $backendRoot 'Data\AppDbContext.cs'
$modelTarget = Join-Path $backendRoot 'Models\PhieuMuonThietBi.cs'
$baselineHash = (Get-FileHash -LiteralPath (Join-Path $stageRoot 'AppDbContext.original.cs') -Algorithm SHA256).Hash
if ((Get-FileHash -LiteralPath $contextTarget -Algorithm SHA256).Hash -ne $baselineHash) {
    throw 'Backend context changed since preparation; review before applying.'
}
if (Test-Path -LiteralPath $modelTarget) {
    throw 'Equipment snapshot model already exists; review before applying.'
}
Copy-Item -LiteralPath (Join-Path $stageRoot 'backend\Models\PhieuMuonThietBi.cs') -Destination $modelTarget
Copy-Item -LiteralPath (Join-Path $stageRoot 'backend\Data\AppDbContext.cs') -Destination $contextTarget
Write-Output 'Applied equipment snapshot model and EF mapping. Database was not modified.'
