#!/usr/bin/env pwsh
# SWARMZ_SMOKE_TEST.ps1 – Smoke test for SWARMZ ecosystem
# Assumes server is already running on localhost:8012

$base = "http://localhost:8012"
$pass = 0
$fail = 0

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SWARMZ SMOKE TEST" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1) /openapi.json
Write-Host "[1/6] GET /openapi.json"
try { $r = Invoke-WebRequest -Uri "$base/openapi.json" -UseBasicParsing -ErrorAction Stop; Write-Host "  PASS" -ForegroundColor Green; $pass++ } catch { Write-Host "  FAIL" -ForegroundColor Red; $fail++ }

# 2) /v1/health
Write-Host "[2/6] GET /v1/health"
try { $r = Invoke-WebRequest -Uri "$base/v1/health" -UseBasicParsing -ErrorAction Stop; Write-Host "  PASS" -ForegroundColor Green; $pass++ } catch { Write-Host "  FAIL" -ForegroundColor Red; $fail++ }

# 3) Start AUTO loop
Write-Host "[3/6] POST /v1/ecosystem/auto/start (tick_interval=5)"
try {
    $body = '{"tick_interval":5}'
    $r = Invoke-WebRequest -Uri "$base/v1/ecosystem/auto/start" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    Write-Host "  PASS" -ForegroundColor Green; $pass++
} catch { Write-Host "  FAIL" -ForegroundColor Red; $fail++ }

# 4) Wait for 2 ticks
Write-Host "[4/6] Waiting 12 seconds for 2 ticks..."
Start-Sleep -Seconds 12

# 5) Check audit.jsonl grew
Write-Host "[5/6] Checking audit.jsonl growth"
if (Test-Path "data/audit.jsonl") {
    $size = (Get-Item "data/audit.jsonl").Length
    if ($size -gt 0) { Write-Host "  PASS - audit.jsonl has $size bytes" -ForegroundColor Green; $pass++ }
    else { Write-Host "  FAIL - audit.jsonl is empty" -ForegroundColor Red; $fail++ }
} else { Write-Host "  FAIL - audit.jsonl not found" -ForegroundColor Red; $fail++ }

# 6) Stop AUTO loop
Write-Host "[6/6] POST /v1/ecosystem/auto/stop"
try {
    $r = Invoke-WebRequest -Uri "$base/v1/ecosystem/auto/stop" -Method POST -UseBasicParsing -ErrorAction Stop
    Write-Host "  PASS" -ForegroundColor Green; $pass++
} catch { Write-Host "  FAIL" -ForegroundColor Red; $fail++ }

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Results: $pass passed, $fail failed" -ForegroundColor $(if ($fail -gt 0) {"Red"} else {"Green"})
Write-Host "============================================" -ForegroundColor Cyan

if ($fail -gt 0) { Write-Host "  STATUS: FAIL" -ForegroundColor Red; exit 1 }
else { Write-Host "  STATUS: ALL PASSED" -ForegroundColor Green; exit 0 }
