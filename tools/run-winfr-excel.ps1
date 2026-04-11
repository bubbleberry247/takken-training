$exe = "C:\Program Files\WindowsApps\Microsoft.WindowsFileRecovery_0.1.20151.0_x64__8wekyb3d8bbwe\ntfssalv_cli_exe\WinFR.exe"
$log = Join-Path $env:TEMP "winfr-excel-run2.log"

Remove-Item $log -Force -ErrorAction SilentlyContinue

$arguments = @(
    "/c",
    "echo y|`"$exe`" E: C: /extensive /n *.xlsx /n *.xls /n *.xlsm /n *.xlsb > `"$log`" 2>&1"
)

Start-Process -FilePath "cmd.exe" -ArgumentList $arguments -Verb RunAs -WindowStyle Hidden

Write-Output "LOG=$log"
