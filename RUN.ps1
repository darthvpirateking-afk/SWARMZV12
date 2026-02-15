#!/usr/bin/env pwsh
# SWARMZ - One-Command Startup Script (PowerShell)
# Usage: .\RUN.ps1 [--test|--demo|--api]

param(
    [switch]$test,
    [switch]$demo,
    [switch]$api,
    [switch]$help
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SWARMZ - Operator-Sovereign System" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Show help
if ($help) {
    Write-Host "Usage: .\RUN.ps1 [options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  (no args)   Start interactive CLI mode"
    Write-Host "  --test      Run test suite"
    Write-Host "  --demo      Run demo examples"
    Write-Host "  --api       Start API server (requires FastAPI)"
    Write-Host "  --help      Show this help message"
    Write-Host ""
    exit 0
}

# Check Python installation
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python 3\.([6-9]|[1-9][0-9])") {
            $pythonCmd = $cmd
            Write-Host "  ✓ Found: $version" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    Write-Host "  ✗ Error: Python 3.6+ not found" -ForegroundColor Red
    Write-Host "  Please install Python from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# Check/create virtual environment
Write-Host "[2/5] Setting up virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    Write-Host "  Creating new virtual environment..." -ForegroundColor Cyan
    & $pythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "  ✓ Virtual environment exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "  ✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Activation script not found, continuing..." -ForegroundColor Yellow
}

# Install dependencies
Write-Host "[4/5] Installing dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    $pipCmd = "venv\Scripts\pip.exe"
    if (-not (Test-Path $pipCmd)) {
        $pipCmd = "pip"
    }
    
    & $pipCmd install -q -r requirements.txt 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Some dependencies may have failed (optional packages)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ requirements.txt not found, skipping..." -ForegroundColor Yellow
}

# Run appropriate command
Write-Host "[5/5] Starting SWARMZ..." -ForegroundColor Yellow
Write-Host ""

$pythonExe = "venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = $pythonCmd
}

if ($test) {
    Write-Host "Running test suite..." -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    & $pythonExe test_swarmz.py
} elseif ($demo) {
    Write-Host "Running demo examples..." -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    & $pythonExe examples.py
} elseif ($api) {
    Write-Host "Starting API server..." -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    if (Test-Path "swarmz_api.py") {
        Write-Host "API will be available at: http://127.0.0.1:8000" -ForegroundColor Green
        Write-Host "API docs at: http://127.0.0.1:8000/docs" -ForegroundColor Green
        Write-Host ""
        & $pythonExe -m uvicorn swarmz_api:app --host 127.0.0.1 --port 8000
    } else {
        Write-Host "  ✗ swarmz_api.py not found" -ForegroundColor Red
        Write-Host "  Run installer.py to create API components" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "Starting interactive CLI..." -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "Available commands:" -ForegroundColor Green
    Write-Host "  list          - List all capabilities"
    Write-Host "  task <name>   - Execute a task"
    Write-Host "  audit         - View audit log"
    Write-Host "  exit          - Exit interactive mode"
    Write-Host ""
    Write-Host "Quick start:" -ForegroundColor Yellow
    Write-Host "  swarmz> list"
    Write-Host "  swarmz> task echo {`"message`": `"Hello!`"}"
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    & $pythonExe swarmz_cli.py --interactive
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SWARMZ session ended" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
