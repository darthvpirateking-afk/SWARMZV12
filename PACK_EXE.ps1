#!/usr/bin/env pwsh
# PACK_EXE.ps1 — Build a single-file Windows EXE for SWARMZ via PyInstaller
#
# Prerequisites:
#   pip install -r requirements.txt -r requirements-dev.txt
#
# Usage:
#   .\PACK_EXE.ps1

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SWARMZ — Build single-file Windows EXE"    -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Ensure PyInstaller is available
try {
    $piVer = & python -m pyinstaller --version 2>&1
    Write-Host "  PyInstaller version: $piVer" -ForegroundColor Green
} catch {
    Write-Host "  PyInstaller not found. Install it first:" -ForegroundColor Red
    Write-Host "    pip install -r requirements-dev.txt"     -ForegroundColor Yellow
    exit 1
}

Write-Host "  Building EXE …" -ForegroundColor Yellow

python -m PyInstaller `
    --onefile `
    --name swarmz `
    --add-data "swarmz_runtime;swarmz_runtime" `
    --add-data "plugins;plugins" `
    --add-data "config.json;." `
    --hidden-import uvicorn.logging `
    --hidden-import uvicorn.loops `
    --hidden-import uvicorn.loops.auto `
    --hidden-import uvicorn.protocols `
    --hidden-import uvicorn.protocols.http `
    --hidden-import uvicorn.protocols.http.auto `
    --hidden-import uvicorn.protocols.websockets `
    --hidden-import uvicorn.protocols.websockets.auto `
    --hidden-import uvicorn.lifespan `
    --hidden-import uvicorn.lifespan.on `
    run_swarmz.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "  ✓ Build succeeded!" -ForegroundColor Green
    Write-Host "  EXE: dist\swarmz.exe" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "  ✗ Build failed." -ForegroundColor Red
    exit 1
}
