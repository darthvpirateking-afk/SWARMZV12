#!/usr/bin/env pwsh
# SWARMZ_UP.ps1 – Start SWARMZ in AUTO mode (AUTO=1)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SWARMZ - AUTO MODE STARTUP" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$env:AUTO = "1"
$env:TICK_INTERVAL = "30"

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

Write-Host "Starting SWARMZ (AUTO=1, TICK_INTERVAL=$env:TICK_INTERVAL)..." -ForegroundColor Green
& $py run_swarmz.py
