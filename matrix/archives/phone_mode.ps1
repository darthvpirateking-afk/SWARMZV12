# SWARMZ Phone Mode Launcher (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SWARMZ PHONE MODE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ ERROR: Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$lanIp = python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PHONE ACCESS READY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Phone URL: http://$lanIp`:8012/" -ForegroundColor Green
Write-Host "Health:    http://$lanIp`:8012/v1/health" -ForegroundColor Green
Write-Host "AI Chat:   POST http://$lanIp`:8012/v1/nexusmon/chat" -ForegroundColor Green
Write-Host ""
Write-Host "Use the same Wi-Fi network on phone + PC." -ForegroundColor Yellow
Write-Host ""

python run_server.py --host 0.0.0.0 --port 8012

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "✗ ERROR: Server stopped with error code $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
