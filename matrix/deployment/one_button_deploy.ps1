#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "SWARMZ One-Button Deploy" -ForegroundColor Cyan

$Port = if ($env:PORT) { [int]$env:PORT } else { 8012 }
$HostBind = if ($env:HOST_BIND) { $env:HOST_BIND } else { "0.0.0.0" }

$venvPy = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
  Write-Host "Creating venv..." -ForegroundColor Yellow
  python -m venv venv
}

if (-not (Test-Path $venvPy)) {
  Write-Host "[ERROR] python venv not available" -ForegroundColor Red
  exit 1
}

Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $venvPy -m pip install -U pip | Out-Null
& $venvPy -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")

if (-not (Test-Path (Join-Path $PSScriptRoot "docs\WORLD_BIBLE.md"))) {
  Write-Host "[WARN] docs/WORLD_BIBLE.md not found" -ForegroundColor Yellow
}

$env:PORT = "$Port"
$env:HOST = $HostBind

Write-Host ("Starting SWARMZ at http://127.0.0.1:{0}" -f $Port) -ForegroundColor Green
Start-Process ("http://127.0.0.1:{0}/" -f $Port) | Out-Null

if (Test-Path (Join-Path $PSScriptRoot "run_server.py")) {
  & $venvPy (Join-Path $PSScriptRoot "run_server.py") --host $HostBind --port $Port
  exit $LASTEXITCODE
}

& $venvPy -m uvicorn swarmz_runtime.api.server:app --host $HostBind --port $Port
exit $LASTEXITCODE
