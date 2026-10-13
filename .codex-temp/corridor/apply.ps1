$ErrorActionPreference = 'Stop'
$taskRoot = 'E:\EAUT\Khoi_nghiep_sang_tao\ClassHub\Frontend\.codex-temp\corridor\backend'
$backendRoot = 'E:\EAUT\Khoi_nghiep_sang_tao\ClassHub\Backend\ClassHub-API\ClassHub-API'
$files = @('Models\PhongHoc.cs', 'Controllers\RoomsController.cs', 'Controllers\AssetsController.cs', 'Controllers\AdminBuildingsController.cs', 'Controllers\DamageReportsController.cs')
foreach ($file in $files) {
    $target = [IO.Path]::GetFullPath((Join-Path $backendRoot $file))
    if (-not $target.StartsWith($backendRoot + '\')) { throw 'Unexpected backend path' }
    Copy-Item -LiteralPath (Join-Path $taskRoot $file) -Destination $target -Force
}
Write-Output 'Applied corridor cabinet and damage report backend changes.'
