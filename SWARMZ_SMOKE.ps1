#!/usr/bin/env pwsh
# SWARMZ_SMOKE.ps1 — smoke test (PS 5.1 safe, no $Host, no ??)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "SWARMZ_SMOKE" -ForegroundColor Cyan

$Base = "http://127.0.0.1:8012"
if ($env:BASE_URL) { $Base = $env:BASE_URL.TrimEnd('/') }

function Call-Endpoint($method, $uri, $body) {
  $hdrs = @{}
  if ($env:OPERATOR_KEY) { $hdrs["x-operator-key"] = $env:OPERATOR_KEY }
  if ($method -eq "GET") {
    return Invoke-RestMethod -Method Get -Uri $uri -Headers $hdrs -TimeoutSec 10
  }
  return Invoke-RestMethod -Method $method -Uri $uri -Headers $hdrs `
    -Body ($body | ConvertTo-Json -Compress) -ContentType "application/json" -TimeoutSec 10
}

# 1. /health
try {
  $h = Call-Endpoint GET "$Base/health" $null
  if ($h.status -ne "ok") { throw "status not ok" }
  Write-Host "1/3 Health OK" -ForegroundColor Green
} catch {
  Write-Host ("1/3 Health FAIL: {0}" -f $_) -ForegroundColor Red; exit 1
}

# 2. /v1/ui/state
try {
  $ui = Call-Endpoint GET "$Base/v1/ui/state" $null
  if (-not $ui.ok) { throw "ok not true" }
  Write-Host "2/3 UI State OK" -ForegroundColor Green
} catch {
  Write-Host ("2/3 UI State FAIL: {0}" -f $_) -ForegroundColor Red; exit 1
}

# 3. /v1/missions/list
try {
  $ml = Call-Endpoint GET "$Base/v1/missions/list" $null
  if (-not $ml.ok) { throw "ok not true" }
  Write-Host "3/3 Missions List OK" -ForegroundColor Green
} catch {
  Write-Host ("3/3 Missions List FAIL: {0}" -f $_) -ForegroundColor Red; exit 1
}

Write-Host "ALL SMOKE TESTS PASSED" -ForegroundColor Green
exit 0
