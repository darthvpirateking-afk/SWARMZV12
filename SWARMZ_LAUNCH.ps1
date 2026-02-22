# SWARMZ - Bulletproof Launcher
# Handles all the messy stuff automatically

Write-Host "🚀 SWARMZ Enhanced Launcher" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan

# Kill any existing processes on port 8012
Write-Host "🔧 Cleaning up existing processes..." -ForegroundColor Yellow
$pids = netstat -ano 2>$null | Select-String ':8012.*LISTENING' | ForEach-Object { ($_.Line -split '\s+')[-1] } | Where-Object { $_ -match '^\d+$' } | Select-Object -Unique
foreach($p in $pids) {
    Stop-Process -Id ([int]$p) -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Killed process $p" -ForegroundColor Green
}

# Wait a moment for ports to free up
Start-Sleep -Seconds 2

# Set up environment
Write-Host "🔧 Setting up environment..." -ForegroundColor Yellow
$env:PORT = '8012'
$env:PYTHONPATH = (Get-Location).Path

# Start with proper error handling
Write-Host "🚀 Starting Enhanced SWARMZ Server..." -ForegroundColor Green
Write-Host "   📡 Interface: http://localhost:8012" -ForegroundColor Cyan
Write-Host "   🤖 Enhanced AI: ACTIVE" -ForegroundColor Cyan
Write-Host "   🎨 Avatar System: READY" -ForegroundColor Cyan
Write-Host ""

try {
    & ".\.venv\Scripts\python.exe" run_server.py
} catch {
    Write-Host "❌ Error starting server: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "🔍 Checking for issues..." -ForegroundColor Yellow
    
    # Quick diagnosis
    if (-not (Test-Path ".venv")) {
        Write-Host "   ⚠️ Virtual environment missing - run: python -m venv .venv" -ForegroundColor Yellow
    }
    if (-not (Test-Path "run_server.py")) {
        Write-Host "   ⚠️ Server file missing" -ForegroundColor Yellow
    }
    
    Read-Host "Press Enter to exit"
}