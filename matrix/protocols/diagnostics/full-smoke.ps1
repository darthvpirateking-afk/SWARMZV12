#!/usr/bin/env pwsh
# SWARMZ_SMOKE_TEST.ps1 – Full-flow smoke test for SWARMZ ecosystem
# Assumes server is already running on localhost:8012 (with swarm runner)

$base = "http://localhost:8012"
$pass = 0
$fail = 0

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SWARMZ SMOKE TEST" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1) GET /v1/health
Write-Host "[1/7] GET /v1/health"
try {
    $r = Invoke-WebRequest -Uri "$base/v1/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "  PASS" -ForegroundColor Green; $pass++
} catch { Write-Host "  FAIL" -ForegroundColor Red; $fail++ }

# 2) GET /v1/swarm/status  — runner must be "up"
Write-Host "[2/7] GET /v1/swarm/status (runner up)"
try {
    $r = Invoke-WebRequest -Uri "$base/v1/swarm/status" -UseBasicParsing -ErrorAction Stop
    $body = $r.Content | ConvertFrom-Json
    if ($body.runner -eq "up") { Write-Host "  PASS – runner is up" -ForegroundColor Green; $pass++ }
    else { Write-Host "  FAIL – runner status: $($body.runner)" -ForegroundColor Red; $fail++ }
} catch { Write-Host "  FAIL – could not reach /v1/swarm/status" -ForegroundColor Red; $fail++ }

# 3) POST /v1/mode  — switch to BUILD
Write-Host "[3/7] POST /v1/mode -> BUILD"
try {
    $modeBody = '{"mode":"BUILD"}'
    $r = Invoke-WebRequest -Uri "$base/v1/mode" -Method POST -Body $modeBody -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $body = $r.Content | ConvertFrom-Json
    if ($body.mode -eq "BUILD") { Write-Host "  PASS" -ForegroundColor Green; $pass++ }
    else { Write-Host "  FAIL – mode: $($body.mode)" -ForegroundColor Red; $fail++ }
} catch { Write-Host "  FAIL – could not switch mode" -ForegroundColor Red; $fail++ }

# 4) POST /v1/build/dispatch  — create a smoke mission
Write-Host "[4/7] POST /v1/build/dispatch (intent=smoke)"
$missionId = ""
try {
    $dispatchBody = '{"intent":"smoke","spec":{}}'
    $r = Invoke-WebRequest -Uri "$base/v1/build/dispatch" -Method POST -Body $dispatchBody -ContentType "application/json" -UseBasicParsing -ErrorAction Stop
    $body = $r.Content | ConvertFrom-Json
    $missionId = $body.mission_id
    if ($missionId -ne "") { Write-Host "  PASS – mission_id: $missionId" -ForegroundColor Green; $pass++ }
    else { Write-Host "  FAIL – no mission_id returned" -ForegroundColor Red; $fail++ }
} catch { Write-Host "  FAIL – could not dispatch" -ForegroundColor Red; $fail++ }

# 5) Wait for runner to pick it up
Write-Host "[5/7] Waiting 3 seconds for runner..."
Start-Sleep -Seconds 3

# 6) GET /v1/missions/list  — confirm smoke mission → SUCCESS
Write-Host "[6/7] GET /v1/missions/list (confirm SUCCESS)"
try {
    $r = Invoke-WebRequest -Uri "$base/v1/missions/list" -UseBasicParsing -ErrorAction Stop
    $body = $r.Content | ConvertFrom-Json
    $found = $false
    foreach ($m in $body.missions) {
        if ($m.mission_id -eq $missionId -and $m.status -eq "SUCCESS") { $found = $true; break }
    }
    if ($found) { Write-Host "  PASS – mission $missionId is SUCCESS" -ForegroundColor Green; $pass++ }
    else { Write-Host "  FAIL – mission not found or not SUCCESS" -ForegroundColor Red; $fail++ }
} catch { Write-Host "  FAIL – could not list missions" -ForegroundColor Red; $fail++ }

# 7) Confirm packs/<id>/result.json exists
Write-Host "[7/7] Check packs/$missionId/result.json"
if ($missionId -ne "" -and (Test-Path "packs/$missionId/result.json")) {
    Write-Host "  PASS" -ForegroundColor Green; $pass++
} else {
    Write-Host "  FAIL – result.json not found" -ForegroundColor Red; $fail++
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Results: $pass passed, $fail failed" -ForegroundColor $(if ($fail -gt 0) {"Red"} else {"Green"})
Write-Host "============================================" -ForegroundColor Cyan

if ($fail -gt 0) { Write-Host "  STATUS: FAIL" -ForegroundColor Red; exit 1 }
else { Write-Host "  STATUS: ALL PASSED" -ForegroundColor Green; exit 0 }
