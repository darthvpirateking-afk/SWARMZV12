Param(
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

$existing = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existing) {
  Write-Host "Cockpit server already listening on http://$BindHost`:$Port"
  exit 0
}

Start-Process -FilePath $python -ArgumentList "run_server.py --host $BindHost --port $Port" -WorkingDirectory $root -WindowStyle Hidden | Out-Null
Start-Sleep -Seconds 2

$up = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $up) {
  Write-Error "Server failed to start on port $Port"
}

Write-Host "Cockpit server started."
Write-Host "Open:"
Write-Host "  http://$BindHost`:$Port/"
Write-Host "  http://$BindHost`:$Port/cockpit/"
Write-Host "Legacy routes /organism and /console now redirect to /cockpit/"
