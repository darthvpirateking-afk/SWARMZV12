#!/usr/bin/env pwsh
# SWARMZ_UP.ps1 – Start SWARMZ in AUTO mode (AUTO=1)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SWARMZ - AUTO MODE STARTUP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$env:AUTO = "1"
$env:TICK_INTERVAL = "30"
if (-not $env:OFFLINE_MODE) { $env:OFFLINE_MODE = "0" }
$hostBind = "0.0.0.0"
$port = 8012
$baseUrl = "http://localhost:8012"

# Locate Python
$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try { $v = & $cmd --version 2>&1; if ($LASTEXITCODE -eq 0) { $pythonCmd = $cmd; break } } catch {}
}
if (-not $pythonCmd) { Write-Host "Python 3 not found" -ForegroundColor Red; exit 1 }

# Create venv if missing
if (-not (Test-Path "venv")) { & $pythonCmd -m venv venv }

# Install deps
$pip = "venv\Scripts\pip.exe"
if (-not (Test-Path $pip)) { $pip = "pip" }
& $pip install -q -r requirements.txt 2>&1 | Out-Null

$py = "venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = $pythonCmd }

Write-Host "Running self_check..." -ForegroundColor Yellow
& $py tools\self_check.py
if ($LASTEXITCODE -ne 0) { Write-Host "self_check reported issues (continuing)..." -ForegroundColor Yellow }

if (Test-Path "config/runtime.json") {
    try {
        $cfg = Get-Content -Raw "config/runtime.json" | ConvertFrom-Json
        if ($cfg.bind) { $hostBind = $cfg.bind }
        if ($cfg.port) { $port = [int]$cfg.port }
        if ($cfg.apiBaseUrl) { $baseUrl = $cfg.apiBaseUrl }
        if ($cfg.offlineMode) { $env:OFFLINE_MODE = "1" }
    } catch {}
}

Write-Host "Opening UI..." -ForegroundColor Cyan
Start-Process "$baseUrl/app"

Write-Host "Starting SWARMZ (AUTO=1, TICK_INTERVAL=$env:TICK_INTERVAL)..." -ForegroundColor Green
& $py run_server.py --host $hostBind --port $port
