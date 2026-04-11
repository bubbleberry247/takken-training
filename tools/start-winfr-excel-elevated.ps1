Add-Type -AssemblyName Microsoft.VisualBasic

$exe = "C:\Program Files\WindowsApps\Microsoft.WindowsFileRecovery_0.1.20151.0_x64__8wekyb3d8bbwe\ntfssalv_cli_exe\WinFR.exe"
$trace = "C:\ProgramData\Generative AI\Github\doboku-14w-training\tools\winfr-helper-trace.log"
$arguments = @(
    "E:",
    "C:",
    "/extensive",
    "/n",
    "*.xlsx",
    "/n",
    "*.xls",
    "/n",
    "*.xlsm",
    "/n",
    "*.xlsb"
)

Remove-Item $trace -Force -ErrorAction SilentlyContinue
Add-Content -Path $trace -Value "helper:start $(Get-Date -Format o)"

Get-Process WinFR -ErrorAction SilentlyContinue | Stop-Process -Force
Add-Content -Path $trace -Value "helper:stopped-existing $(Get-Date -Format o)"
Start-Sleep -Seconds 1

$process = Start-Process -FilePath $exe -ArgumentList $arguments -PassThru
Add-Content -Path $trace -Value ("helper:started pid={0} {1}" -f $process.Id, (Get-Date -Format o))

for ($i = 0; $i -lt 40; $i++) {
    if ($process.HasExited) {
        break
    }

    $process.Refresh()

    if ($process.MainWindowHandle -ne 0) {
        Add-Content -Path $trace -Value ("helper:window handle={0} {1}" -f $process.MainWindowHandle, (Get-Date -Format o))
        break
    }

    Start-Sleep -Milliseconds 250
}

if (-not $process.HasExited) {
    [Microsoft.VisualBasic.Interaction]::AppActivate($process.Id) | Out-Null
    Start-Sleep -Milliseconds 500

    $shell = New-Object -ComObject WScript.Shell

    for ($i = 0; $i -lt 3; $i++) {
        $shell.SendKeys("Y~")
        Add-Content -Path $trace -Value ("helper:sendkeys iteration={0} {1}" -f $i, (Get-Date -Format o))
        Start-Sleep -Milliseconds 500
    }
}

Add-Content -Path $trace -Value ("helper:end {0}" -f (Get-Date -Format o))
Write-Output ("PID={0}" -f $process.Id)
