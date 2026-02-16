#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

function Assert-Ok($resp, $label) {
    if (-not $resp) { throw "$label failed" }
}

Write-Host "Health..." -ForegroundColor Cyan
$health = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8012/health"
Assert-Ok $health "health"

Write-Host "Dispatch..." -ForegroundColor Cyan
$payload = @{ intent = "smoke"; scope = @{ test = "ok" } }
$dispatch = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8012/v1/sovereign/dispatch" -ContentType "application/json" -Body ($payload | ConvertTo-Json)
Assert-Ok $dispatch "dispatch"

Write-Host "Logs..." -ForegroundColor Cyan
$logs = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8012/v1/system/log?tail=5"
Assert-Ok $logs "logs"

Write-Host "SMOKE PASSED" -ForegroundColor Green
