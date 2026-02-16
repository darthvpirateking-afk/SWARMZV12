# SWARMZ - Build Single-File Windows Executable
# Uses PyInstaller to create a standalone executable

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SWARMZ - Build Windows Executable" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Create/activate virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies including dev dependencies
Write-Host "Installing build dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
pip install -r requirements-dev.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Clean previous builds
if (Test-Path "dist") {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist"
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
}

# Build the executable
Write-Host "Building SWARMZ executable..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

pyinstaller --onefile `
    --name SWARMZ `
    --icon NONE `
    --add-data "plugins;plugins" `
    --add-data "config.json;." `
    --hidden-import uvicorn `
    --hidden-import fastapi `
    --hidden-import pydantic `
    --collect-all uvicorn `
    --collect-all fastapi `
    swarmz_server.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ ERROR: Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Build successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Executable location: dist\SWARMZ.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the server:" -ForegroundColor Yellow
Write-Host "  cd dist" -ForegroundColor White
Write-Host "  .\SWARMZ.exe" -ForegroundColor White
Write-Host ""
Write-Host "Note: The executable includes all dependencies and can run without Python installed" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"
