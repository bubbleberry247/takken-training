$base = "C:\Users\owner\AppData\Local\Microsoft\WinGet\Packages\CGSecurity.TestDisk_Microsoft.Winget.Source_8wekyb3d8bbwe\testdisk-7.3-WIP"
$exe = Join-Path $base "photorec_win.exe"
$dest = "C:\PhotoRecRecovery"
$log = Join-Path $dest "photorec-excel.log"
$out = Join-Path $dest "photorec-excel.out"

New-Item -ItemType Directory -Force -Path $dest | Out-Null
Remove-Item $log, $out -Force -ErrorAction SilentlyContinue

$arguments = @(
    "/log",
    "/logname", $log,
    "/d", $dest,
    "/cmd", "\\.\PhysicalDrive2",
    "partition_i386,fileopt,everything,disable,xls,enable,xlsx,enable,1,freespace,search"
)

& $exe @arguments *>&1 | Out-File $out -Encoding utf8
