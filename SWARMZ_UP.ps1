#!/usr/bin/env pwsh
# SWARMZ_UP.ps1 — robust launcher for older PowerShell (no ??, no $Host, no $lan: parsing bugs)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "SWARMZ_UP" -ForegroundColor Cyan

# Config
$Port = if ($env:PORT) { [int]$env:PORT } else { 8012 }
$HostBind = "0.0.0.0"  # DO NOT use $Host (reserved)

function Find-Python {
  foreach ($cmd in @("python3", "python")) {
    try {
      & $cmd --version 2>$null | Out-Null
      if ($LASTEXITCODE -eq 0) { return $cmd }
    } catch {}
  }
  return $null
}

function Get-LanIp {
  try {
    $udp = New-Object System.Net.Sockets.UdpClient
    $udp.Connect("8.8.8.8", 53)
    $ip = $udp.Client.LocalEndPoint.Address.ToString()
    $udp.Close()
    return $ip
  } catch {
    return $null
  }
}

function Get-ListeningPid($port) {
  # netstat works everywhere; parse LISTENING lines for this port
  $lines = netstat -ano | Select-String -Pattern (":$port\s") | Select-String -Pattern "LISTENING"
  foreach ($l in $lines) {
    $parts = ($l.Line -split "\s+") | Where-Object { $_ -ne "" }
    if ($parts.Count -ge 5) {
      $listenPid = $parts[-1]
      if ($listenPid -match "^\d+$") { return [int]$listenPid }
    }
  }
  return $null
}

# Ensure venv
$venvPy = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
  $py = Find-Python
  if (-not $py) { Write-Host "[ERROR] Python 3 not found in PATH." -ForegroundColor Red; exit 1 }

  Write-Host "Creating venv..." -ForegroundColor Yellow
  & $py -m venv (Join-Path $PSScriptRoot "venv")
}

if (-not (Test-Path $venvPy)) { Write-Host "[ERROR] venv python missing: $venvPy" -ForegroundColor Red; exit 1 }

# Install deps (quiet)
Write-Host "Installing requirements..." -ForegroundColor Yellow
& $venvPy -m pip install -U pip 2>$null | Out-Null
& $venvPy -m pip install -r (Join-Path $PSScriptRoot "requirements.txt") 2>$null | Out-Null

# Port check / optional auto-kill
$listenPid = Get-ListeningPid $Port
if ($listenPid) {
  Write-Host "[WARN] Port $Port already LISTENING (PID $listenPid)." -ForegroundColor Yellow
  if ($env:KILL_PORT -eq "1") {
    Write-Host "KILL_PORT=1 set → stopping PID $listenPid..." -ForegroundColor Yellow
    Stop-Process -Id $listenPid -Force
    Start-Sleep -Seconds 1
    $pid2 = Get-ListeningPid $Port
    if ($pid2) { Write-Host "[ERROR] Port still in use (PID $pid2)." -ForegroundColor Red; exit 1 }
  } else {
    Write-Host "Fix: close that process, OR run: `$env:KILL_PORT=1; .\SWARMZ_UP.ps1" -ForegroundColor Yellow
    exit 1
  }
}

# URLs
$lan = Get-LanIp
Write-Host ("LOCAL: http://127.0.0.1:{0}/" -f $Port) -ForegroundColor Cyan
if ($lan) {
  # IMPORTANT: braces prevent PowerShell interpreting "$lan:" as a drive
  Write-Host ("LAN:   http://{0}:{1}/" -f $lan, $Port) -ForegroundColor Cyan
}

# Open UI
Start-Process ("http://127.0.0.1:{0}/" -f $Port) | Out-Null

# Start server

if (Test-Path (Join-Path $PSScriptRoot "run_server.py")) {
  Write-Host ("Starting server via run_server.py on {0}:{1}" -f $HostBind, $Port) -ForegroundColor Green
  & $venvPy (Join-Path $PSScriptRoot "run_server.py") --host $HostBind --port $Port
  exit $LASTEXITCODE
}

if (Test-Path (Join-Path $PSScriptRoot "server.py")) {
  Write-Host ("run_server.py missing → starting via uvicorn server:app on {0}:{1}" -f $HostBind, $Port) -ForegroundColor Green
  & $venvPy -m uvicorn server:app --host $HostBind --port $Port
  exit $LASTEXITCODE
}

Write-Host "[ERROR] Missing run_server.py and server.py. Your repo has no server entrypoint." -ForegroundColor Red
Write-Host "Tell your agent: create server.py (FastAPI app) + run_server.py (uvicorn runner)." -ForegroundColor Red
exit 1
