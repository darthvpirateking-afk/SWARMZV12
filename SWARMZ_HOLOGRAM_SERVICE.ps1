# ---------- helpers ----------
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
#!/usr/bin/env pwsh
# SWARMZ_HOLOGRAM_SERVICE.ps1 — Windows service launcher for SWARMZ hologram system

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "SWARMZ_HOLOGRAM_SERVICE" -ForegroundColor Cyan

# ---------- config ----------
$Port = 8020  # Default port for hologram service
if ($env:PORT) { $Port = [int]$env:PORT }
$HostBind = "0.0.0.0"

# ---------- helpers ----------
function Find-Python {
  foreach ($cmd in @("python3","python")) {
    try {
      & $cmd --version 2>$null | Out-Null
      if ($LASTEXITCODE -eq 0) { return $cmd }
    } catch {}
  }
  return $null
}

function Get-ListeningPid($targetPort) {
  $lines = netstat -ano | Select-String -Pattern (":$targetPort\\s") | Select-String -Pattern "LISTENING"
  foreach ($l in $lines) {
    $parts = ($l.Line -split "\\s+") | Where-Object { $_ -ne "" }
    if ($parts.Count -ge 5) {
      $tok = $parts[-1]
      if ($tok -match "^\\d+$") { return [int]$tok }
    }
  }
  return $null
}

function Show-Urls($lanIp, $p) {
  Write-Host ("LOCAL: http://127.0.0.1:{0}/" -f $p) -ForegroundColor Cyan
  if ($lanIp) { Write-Host ("LAN:   http://{0}:{1}/" -f $lanIp,$p) -ForegroundColor Cyan }
  Write-Host "PHONE: open LAN URL on same Wi-Fi" -ForegroundColor Cyan
}

# ---------- venv ----------
$venvPy = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
  $py = Find-Python
  if (-not $py) { Write-Host '[ERROR] Python 3 not found.' -ForegroundColor Red; exit 1 }
  Write-Host "Creating venv..." -ForegroundColor Yellow
  & $py -m venv (Join-Path $PSScriptRoot "venv")
}
if (-not (Test-Path $venvPy)) { Write-Host '[ERROR] venv python missing.' -ForegroundColor Red; exit 1 }

# deps (quiet)
$reqFile = Join-Path $PSScriptRoot "swarmz_runtime_requirements.txt"
if (Test-Path $reqFile) {
  Write-Host "Installing requirements..." -ForegroundColor Yellow
  & $venvPy -m pip install -U pip 2>$null | Out-Null
  & $venvPy -m pip install -r $reqFile 2>$null | Out-Null
}

# ---------- port check ----------
$existingPid = Get-ListeningPid $Port
if ($existingPid) {
  Write-Host ("[WARN] Port {0} already LISTENING (PID {1})." -f $Port,$existingPid) -ForegroundColor Yellow
  if ($env:KILL_PORT -eq "1") {
    Write-Host ("KILL_PORT=1 - stopping PID {0}..." -f $existingPid) -ForegroundColor Yellow
    Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    $stillUp = Get-ListeningPid $Port
    if ($stillUp) { Write-Host '[ERROR] Port still in use.' -ForegroundColor Red; exit 1 }
  } else {
    Write-Host "Server already running:" -ForegroundColor Yellow
    Show-Urls (Get-LanIp) $Port
    exit 0
  }
}

# ---------- URLs ----------
$lan = Get-LanIp
Show-Urls $lan $Port

# ---------- start ----------
$env:PORT = "$Port"
if (Test-Path (Join-Path $PSScriptRoot "run_hologram.py")) {
  Write-Host ("Starting run_hologram.py on {0}:{1}" -f $HostBind,$Port) -ForegroundColor Green
  & $venvPy (Join-Path $PSScriptRoot "run_hologram.py") --host $HostBind --port $Port
  exit $LASTEXITCODE
}
Write-Host '[ERROR] No run_hologram.py found.' -ForegroundColor Red
exit 1