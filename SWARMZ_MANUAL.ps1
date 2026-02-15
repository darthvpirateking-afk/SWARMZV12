#!/usr/bin/env pwsh
# SWARMZ_MANUAL.ps1 – Start SWARMZ in MANUAL mode (AUTO=0)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SWARMZ - MANUAL MODE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$env:AUTO = "0"

$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try { $v = & $cmd --version 2>&1; if ($LASTEXITCODE -eq 0) { $pythonCmd = $cmd; break } } catch {}
}
if (-not $pythonCmd) { Write-Host "Python 3 not found" -ForegroundColor Red; exit 1 }

if (-not (Test-Path "venv")) { & $pythonCmd -m venv venv }

$pip = "venv\Scripts\pip.exe"
if (-not (Test-Path $pip)) { $pip = "pip" }
& $pip install -q -r requirements.txt 2>&1 | Out-Null

$py = "venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = $pythonCmd }

Write-Host "Starting SWARMZ (AUTO=0 - manual endpoints only)..." -ForegroundColor Green
& $py run_swarmz.py
